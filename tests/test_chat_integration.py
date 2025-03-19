import json
import pytest
from app import chat_integration
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)

from app.chat_integration import (
    process_tool_calls,
    create_stream_message,
)


class DummyChoice:
    def __init__(self, message=None, delta=None):
        self.message = message
        self.delta = delta or DummyDelta()


class DummyDelta:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []


class DummyStreamChunk:
    def __init__(self, delta):
        # Имитация отдельного чанка (порции данных) ответа при потоковой передаче.
        self.choices = [DummyChoice(delta=delta)]


class DummyToolCallFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = json.dumps(arguments)

    def dict(self):
        # Возвращает словарное представление вызова функции.
        return {"name": self.name, "arguments": self.arguments, "id": "1", "index": 0}


class DummyToolCall:
    def __init__(self, func_name, arguments, tool_call_id="2", index=0):
        self.id = tool_call_id
        self.index = index
        self.function = DummyToolCallFunction(func_name, arguments)


class DummyWebsocket:
    def __init__(self):
        self.sent_texts = []

    async def send_text(self, text: str):
        # Отправка текста через имитированный websocket.
        self.sent_texts.append(text)


class DummyConnectionManager:
    def __init__(self):
        self.messages = []

    def add_message(self, websocket, message):
        # Добавляет сообщение в список хранящихся сообщений.
        self.messages.append(message)


@pytest.mark.asyncio
async def test_process_tool_calls(monkeypatch):
    """
    Тестирует асинхронную функцию process_tool_calls.

    Проверяется обработка вызовов инструментов, связанных с сообщениями,
    а также корректная интеграция с подменой функционала получения данных.
    """
    dummy_tool_call = ChatCompletionMessageToolCall(
        function=Function(name="get_weather", arguments='{"location": "Moscow"}'),
        id="2",
        type="function",
    )
    message_obj = ChatCompletionMessage(
        role="assistant", content="Test content", tool_calls=[dummy_tool_call]
    )
    dummy_websocket = DummyWebsocket()
    dummy_conn_manager = DummyConnectionManager()

    monkeypatch.setattr(
        chat_integration, "get_weather", lambda loc: f"Weather for {loc}"
    )
    monkeypatch.setattr(chat_integration, "get_dollar_rate", lambda: "Dollar rate")
    monkeypatch.setattr(
        chat_integration, "get_weekly_news", lambda query: f"News about {query}"
    )

    responses = await process_tool_calls(
        message_obj, dummy_websocket, dummy_conn_manager
    )

    assert len(responses) == 1
    response = responses[0]

    assert isinstance(response, dict)
    assert "content" in response
    assert "Weather for Moscow" in response["content"]

    # Проверяем, что менеджер соединений получил два сообщения (например, уведомление и ответ)
    assert len(dummy_conn_manager.messages) == 2


@pytest.mark.asyncio
async def test_create_stream_message(monkeypatch):
    """
    Тестирует функцию create_stream_message, которая создает потоковое сообщение.

    Используя monkeypatch, подменяет метод create, чтобы имитировать передачу данных по частям,
    и проверяет, что итоговое сообщение и отправленные через websocket чанки корректно агрегируются.
    """
    chunk1_delta = DummyDelta(content="Hello, ", tool_calls=[])
    chunk2_delta = DummyDelta(content="World!", tool_calls=[])
    dummy_chunks = [DummyStreamChunk(chunk1_delta), DummyStreamChunk(chunk2_delta)]

    async def dummy_create(*, model, messages, tools, stream):
        async def inner():
            for chunk in dummy_chunks:
                yield chunk

        return inner()

    monkeypatch.setattr(
        chat_integration.openai.chat.completions, "create", dummy_create
    )

    dummy_websocket = DummyWebsocket()
    history = [{"role": "user", "content": "Stream test"}]
    result_message = await create_stream_message(history, dummy_websocket)

    # Проверяем, что итоговый контент собран из всех чанков
    assert result_message.content == "Hello, World!"
    # Проверяем, что отправленные через websocket тексты соответствуют содержимому чанков
    assert dummy_websocket.sent_texts == ["Hello, ", "World!"]
