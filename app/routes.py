from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from loguru import logger
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)

from app.chat_integration import create_stream_message, process_tool_calls
from app.config import USER
from app.connections import ConnectionManager

router: APIRouter = APIRouter()
manager: ConnectionManager = ConnectionManager()


@router.websocket("/api/chat/")
async def chat_endpoint(websocket: WebSocket) -> None:
    """
    Обработчик WebSocket для чата.
    """
    await manager.connect(websocket)
    try:
        while True:
            data: str = await websocket.receive_text()
            logger.info("Получено сообщение от клиента: {}", data)

            user_message: ChatCompletionUserMessageParam = (
                ChatCompletionUserMessageParam(role=USER, content=data)
            )
            manager.add_message(websocket, user_message)

            history: Any = manager.get_history(websocket)
            # Первый вызов ChatGPT - ответ ассистента на сообщение пользователя
            assistant_message = await create_stream_message(history, websocket)

            # Если ассистент вызвал инструменты, обрабатываем их
            if assistant_message.tool_calls:
                await process_tool_calls(assistant_message, websocket, manager)
                # Второй вызов ChatGPT с учётом результата работы инструментов
                history = manager.get_history(websocket)
                assistant_message = await create_stream_message(history, websocket)

            logger.success(
                "Отправка сообщения ассистента: {}", assistant_message.content
            )
            # Добавляем финальное сообщение ассистента в историю
            manager.add_message(websocket, assistant_message)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Клиент отключился от WebSocket.")
    except Exception as e:
        logger.exception("Ошибка в процессе обработки чата: {}", e)
        await websocket.close()


@router.get("/", response_class=HTMLResponse)
async def get_index() -> HTMLResponse:
    """
    Эндпоинт для возврата HTML контента главной страницы.
    """
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            html_content: str = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.exception("Ошибка загрузки HTML страницы: {}", e)
        return HTMLResponse(content="Ошибка загрузки страницы.", status_code=500)
