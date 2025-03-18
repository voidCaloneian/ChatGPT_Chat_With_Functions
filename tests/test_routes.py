import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from app.routes import manager
from main import app

client = TestClient(app)


class DummyAssistantMessage:
    def __init__(self, content: str, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []


@pytest.fixture(autouse=True)
def patch_create_stream_message(monkeypatch):
    async def dummy_create_stream_message(history, websocket):
        # Имитация создания потокового сообщения, возвращающего тестовый ответ ассистента.
        return DummyAssistantMessage("dummy response")

    monkeypatch.setattr("app.routes.create_stream_message", dummy_create_stream_message)
    yield


@pytest.fixture(autouse=True)
def patch_process_tool_calls(monkeypatch):
    def dummy_process_tool_calls(message, websocket, manager):
        # Подмена функции обработки вызова инструментов - тестовый стаб.
        pass

    monkeypatch.setattr("app.routes.process_tool_calls", dummy_process_tool_calls)
    yield


def test_get_index_success(monkeypatch):
    dummy_html = "<html><body>Hello World</body></html>"

    def dummy_open(*args, **kwargs):
        # Подмена встроенной функции open для симуляции успешного чтения HTML файла.
        class DummyFile:
            def read(self, *args, **kwargs):
                return dummy_html

            def write(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self  # Возвращаем объект при входе в контекст

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        return DummyFile()

    monkeypatch.setattr("builtins.open", dummy_open)
    response = client.get("/")
    assert response.status_code == 200
    assert dummy_html in response.text


def test_get_index_failure(monkeypatch):
    def dummy_open(*args, **kwargs):
        # Подмена open для симуляции ошибки открытия файла.
        class DummyFile:
            def write(self, *args, **kwargs):
                pass

            def __enter__(self):
                raise Exception(
                    "File not found"
                )  # Генерация ошибки при входе в контекст

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        return DummyFile()

    monkeypatch.setattr("builtins.open", dummy_open)
    response = client.get("/")
    assert response.status_code == 500
    assert "Ошибка загрузки страницы" in response.text


def test_websocket_disconnect(monkeypatch):
    # Подменяем методы подключения и отключения менеджера соединений для контроля поведения.
    async def dummy_connect(ws):
        pass

    monkeypatch.setattr(manager, "connect", dummy_connect)

    def dummy_disconnect(ws):
        pass

    monkeypatch.setattr(manager, "disconnect", dummy_disconnect)

    # Ожидается, что при закрытии вебсокета произойдет исключение WebSocketDisconnect.
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/chat/") as websocket:
            websocket.send_text("Hello WebSocket")
            websocket.close()
