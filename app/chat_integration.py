import json
from typing import Any, Dict, List

from loguru import logger
import openai

from app.api_clients import get_weather, get_dollar_rate, get_weekly_news
from app.models import FunctionCall
from app.config import ASSISTANT
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_tool_message_param import (
    ChatCompletionToolMessageParam,
)
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)

# Инструменты для ChatGPT 😊
tools: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Получить текущую температуру для указанного местоположения.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Город и страна, например: Bogotá, Colombia (на английском)",
                    }
                },
                "required": ["location"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dollar_rate",
            "description": "Получить текущий курс обмена USD к RUB.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weekly_news",
            "description": "Получить последние новости за неделю по указанной теме.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Тема новостей"}
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
]


def process_chat_message(
    history: List[Any],
    tools: List[Dict[str, Any]] = tools,
) -> Any:
    """
    Выполняет первичный вызов ChatGPT с учетом истории сообщений и описания функций.
    """
    completion = openai.chat.completions.create(
        model="gpt-4o", messages=history, tools=tools
    )
    return completion.choices[0].message


def process_tool_calls(
    message: ChatCompletionMessage,
    websocket: Any,
    connection_manager: Any,
) -> List[ChatCompletionToolMessageParam]:
    """
    Обрабатывает вызовы инструментов от ChatGPT.

    :param message: Сообщение от ChatGPT с полем tool_calls.
    :param websocket: Объект WebSocket.
    :param connection_manager: Менеджер соединений.
    :return: Список ответных сообщений инструментов.
    """
    responses: List[ChatCompletionToolMessageParam] = []
    if message.tool_calls:
        logger.info("Модель решила вызвать инструменты.")
        connection_manager.add_message(websocket, message)
        for tool_call in message.tool_calls:
            logger.info("Вызов функции: {}", tool_call.function.name)
            function_call = FunctionCall(
                name=tool_call.function.name,
                arguments=json.loads(tool_call.function.arguments),
            )
            if function_call.name == "get_weather":
                result = get_weather(function_call.arguments.get("location", "None"))
            elif function_call.name == "get_dollar_rate":
                result = get_dollar_rate()
            elif function_call.name == "get_weekly_news":
                result = get_weekly_news(function_call.arguments.get("query", "None"))
            else:
                result = "Функция не найдена."
            logger.info("Ответ функции: {}", result)
            tool_response = ChatCompletionToolMessageParam(
                content=str(result), role="tool", tool_call_id=tool_call.id
            )
            connection_manager.add_message(websocket, tool_response)
            responses.append(tool_response)
    return responses


async def create_stream_message(
    history: List[Any],
    websocket: Any,
) -> ChatCompletionMessage:
    """
    Создает потоковое сообщение для ChatGPT с отправкой частичных результатов через WebSocket.

    :param history: История сообщений для передачи в модель.
    :param websocket: Объект WebSocket для отправки данных клиенту.
    :return: Финальное сообщение ассистента.
    """
    stream = openai.chat.completions.create(
        model="gpt-4o",
        messages=history,
        tools=tools,
        stream=True,
    )

    assistant_text: str = ""
    final_tool_calls: Dict[int, Any] = {}

    for chunk in stream:
        # Сбор данных по вызовам инструментов
        for tool_call in chunk.choices[0].delta.tool_calls or []:
            index: int = tool_call.index
            if index not in final_tool_calls:
                final_tool_calls[index] = tool_call
            else:
                final_tool_calls[
                    index
                ].function.arguments += tool_call.function.arguments

        # Обработка текстового контента
        if chunk.choices[0].delta.content is not None:
            text_chunk: str = chunk.choices[0].delta.content
            assistant_text += text_chunk
            # Отправляем каждую часть через WebSocket клиенту
            await websocket.send_text(text_chunk)

    # Превращаем каждый tool_call в ChatCompletionMessageToolCall
    final_tool_call_objs: List[ChatCompletionMessageToolCall] = [
        ChatCompletionMessageToolCall(**tool_call.dict())
        for tool_call in final_tool_calls.values()
    ]

    logger.success(assistant_text)
    logger.warning(final_tool_call_objs)

    assistant_message = ChatCompletionMessage(
        role=ASSISTANT,
        content=assistant_text,
        tool_calls=final_tool_call_objs if final_tool_call_objs else None,
    )

    return assistant_message
