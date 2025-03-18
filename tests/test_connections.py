import pytest
from app.connections import ConnectionManager


class FakeWebSocket:
    def __init__(self, client="test_client"):
        self._client = client
        self.accept_called = False

    @property
    def client(self):
        return self._client

    async def accept(self):
        # Имитирует вызов метода accept(), который должен выполняться при установлении соединения.
        self.accept_called = True


@pytest.mark.asyncio
async def test_connect():
    """
    Тестирует подключение клиента через ConnectionManager.

    Проверяется вызов метода accept() и инициализация истории с системным сообщением.
    """
    manager = ConnectionManager()
    fake_ws = FakeWebSocket()

    # Вызывается метод подключения, где ожидается вызов fake_ws.accept()
    await manager.connect(fake_ws)
    # Проверяем, что метод accept() был вызван
    assert fake_ws.accept_called is True
    # Получаем историю сообщений для данного websocket
    history = manager.get_history(fake_ws)
    # История должна быть списком и инициализирована с системным сообщением
    assert isinstance(history, list)
    assert len(history) == 1
    system_message = history[0]
    # Проверяем, что сообщение имеет роль "system" и содержит инструкцию с смайликами
    assert system_message["role"] == "system"
    assert "Используй смайлики" in system_message["content"]


def test_disconnect():
    """
    Тестирует отключение клиента через ConnectionManager.

    Проверяется, что websocket удаляется из списка активных соединений при вызове disconnect.
    """
    manager = ConnectionManager()
    fake_ws = FakeWebSocket()
    # Ручное добавление websocket в список активных соединений
    manager.active_connections[fake_ws] = ["dummy_message"]
    # Убеждаемся, что fake_ws присутствует в активных соединениях
    assert fake_ws in manager.active_connections
    # Отключаем websocket
    manager.disconnect(fake_ws)
    # Проверяем, что websocket удален из active_connections
    assert fake_ws not in manager.active_connections


@pytest.mark.asyncio
async def test_add_and_get_message():
    """
    Тестирует добавление нового сообщения и получение истории сообщений через ConnectionManager.

    Убедимся, что новое сообщение корректно добавляется к первоначальной истории.
    """
    manager = ConnectionManager()
    fake_ws = FakeWebSocket()
    await manager.connect(fake_ws)

    # История после подключения должна содержать единственное системное сообщение
    history = manager.get_history(fake_ws)
    assert len(history) == 1

    # Добавляем новое сообщение от пользователя
    message = {"role": "user", "content": "Hello!"}
    manager.add_message(fake_ws, message)
    # Получаем обновленную историю сообщений и проверяем наличие нового сообщения
    history = manager.get_history(fake_ws)
    assert len(history) == 2
    assert history[-1] == message
