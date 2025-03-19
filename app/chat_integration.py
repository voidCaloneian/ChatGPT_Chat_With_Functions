import json
import asyncio
import os
from typing import Any, Dict, List

from loguru import logger
from openai import AsyncOpenAI

from app.api_clients import get_weather, get_dollar_rate, get_weekly_news
from app.config import ASSISTANT
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_tool_message_param import (
    ChatCompletionToolMessageParam,
)
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)


openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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


async def process_tool_calls(
    message: ChatCompletionMessage, websocket: Any, connection_manager: Any
) -> List[ChatCompletionToolMessageParam]:
    """
    Асинхронно обрабатывает вызовы инструментов от ChatGPT и выполняет их параллельно.

    :param message: Сообщение от ChatGPT с полем tool_calls.
    :param websocket: Объект WebSocket.
    :param connection_manager: Менеджер соединений.
    :return: Список ответных сообщений инструментов.
    """
    responses: List[ChatCompletionToolMessageParam] = []

    # Словарь, связывающий имя функции с её реализацией
    tool_functions = {
        "get_weather": lambda args: get_weather(args.get("location", "None")),
        "get_dollar_rate": lambda _: get_dollar_rate(),
        "get_weekly_news": lambda args: get_weekly_news(args.get("query", "None")),
    }

    if message.tool_calls:
        logger.info("Модель решила вызвать инструменты 👍.")
        connection_manager.add_message(websocket, message)

        async def call_tool(tool_call) -> ChatCompletionToolMessageParam:
            func_name = tool_call.function.name
            logger.info("Вызов функции: {}", func_name)

            # Преобразование аргументов в словарь
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as e:
                logger.error("Ошибка декодирования JSON: {}", e)
                arguments = {}

            # Найдем функцию по имени
            function_to_call = tool_functions.get(func_name)
            if function_to_call is None:
                result = f"Функция {func_name} не найдена."
                logger.error(result)
            else:
                # Выполняем функцию в отдельном потоке, чтобы не блокировать event loop
                result = await asyncio.to_thread(function_to_call, arguments)
                logger.info("Ответ функции: {}", result)

            tool_response = ChatCompletionToolMessageParam(
                content=str(result), role="tool", tool_call_id=tool_call.id
            )
            connection_manager.add_message(websocket, tool_response)
            return tool_response

        # Создаем задачи (tasks) для всех вызовов инструментов
        tasks = [call_tool(tool_call) for tool_call in message.tool_calls]
        # Гейзерим выполнение всех задач параллельно
        responses = await asyncio.gather(*tasks)

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
    stream = await openai.chat.completions.create(
        model="gpt-4o",
        messages=history,
        tools=tools,
        stream=True,
    )

    assistant_text: str = ""
    final_tool_calls: Dict[int, Any] = {}

    async for chunk in stream:
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
