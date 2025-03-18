from typing import Any, Dict, List

from fastapi import WebSocket
from loguru import logger
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)


class ConnectionManager:
    """
    Менеджер для управления WebSocket-соединениями с сохранением истории сообщений.
    """

    def __init__(self) -> None:
        self.active_connections: Dict[WebSocket, List[Any]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """
        Устанавливает WebSocket-соединение и инициализирует историю сообщений.

        :param websocket: Объект WebSocket.
        """
        await websocket.accept()
        self.active_connections[websocket] = [
            ChatCompletionSystemMessageParam(
                content=(
                    "Используй смайлики, когда они уместны 😊, "
                    "а также для структурирования текста. Пиши структурированно и по делу, "
                    "минимизируй количество воды. В своих ответах используй Markdown, "
                    "также код оборачивай в ```язык\n<код>\n```."
                ),
                role="system",
            )
        ]
        logger.info("Установлено WebSocket-соединение: {}", websocket.client)

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Разрывает WebSocket-соединение и удаляет его историю сообщений.

        :param websocket: Объект WebSocket.
        """
        if websocket in self.active_connections:
            del self.active_connections[websocket]
            logger.info("WebSocket отключился: {}", websocket.client)

    def get_history(self, websocket: WebSocket) -> List[Any]:
        """
        Возвращает историю сообщений для указанного соединения.

        :param websocket: Объект WebSocket.
        :return: Список сообщений для данного соединения.
        """
        return self.active_connections.get(websocket, [])

    def add_message(self, websocket: WebSocket, message: Any) -> None:
        """
        Добавляет сообщение в историю определённого WebSocket-соединения.

        :param websocket: Объект WebSocket.
        :param message: Сообщение для добавления.
        """
        if websocket in self.active_connections:
            self.active_connections[websocket].append(message)
