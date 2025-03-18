import pytest
import requests
from app.api_clients import get_dollar_rate, get_weather, get_weekly_news


class DummyResponse:
    """
    Имитирует объект ответа, возвращаемого requests.get, для тестирования без реальных HTTP-запросов.
    """

    def __init__(self, json_data, status_code=200):
        """
        Инициализация объекта имитации ответа.

        Args:
            json_data (dict): Данные, возвращаемые методом json().
            status_code (int, optional): HTTP статус-код ответа. По умолчанию 200.
        """
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        """Возвращает данные ответа в формате JSON."""
        return self._json_data

    def raise_for_status(self):
        """
        Генерирует HTTPError, если статус-код не равен 200.
        Имитация стандартного поведения requests.
        """
        if self.status_code != 200:
            raise requests.HTTPError(f"HTTP Error: status code:{self.status_code}")


def test_get_dollar_rate(monkeypatch):
    """
    Тестирует функцию get_dollar_rate.

    Использует monkeypatch для подмены requests.get и проверки корректной обработки
    данных о курсах валют.
    """
    dummy_json = {"conversion_rates": {"RUB": 70, "USD": 1}}

    def dummy_get(url):
        # Имитируем ответ HTTP с предопределенными данными.
        return DummyResponse(dummy_json)

    monkeypatch.setattr(requests, "get", dummy_get)
    result = get_dollar_rate()
    assert "Курсы:" in result, "Сообщение должно содержать текст 'Курсы:'"
    assert "70" in result, "Должен присутствовать курс RUB 70"


def test_get_weather(monkeypatch):
    """
    Тестирует функцию get_weather.

    Подменяет requests.get, чтобы проверить обработку данных о погоде.
    """
    dummy_json = {"weather": [{"description": "ясно"}], "main": {"temp": 20}}

    def dummy_get(url, params):
        # Имитируем ответ сервера с информацией о погоде.
        return DummyResponse(dummy_json)

    monkeypatch.setattr(requests, "get", dummy_get)
    location = "Moscow"
    result = get_weather(location)
    # Проверяем, что результат содержит информацию о температуре или погодном описании
    assert (
        "20" in result or "ясно" in result
    ), "Ответ должен содержать информацию о температуре или описании погоды"


def test_get_weekly_news(monkeypatch):
    """
    Тестирует функцию get_weekly_news.

    Подменяет requests.get для проверки обработки данных о новостях.
    """
    dummy_json = {
        "articles": [{"title": "Test Article", "description": "Test description"}]
    }

    def dummy_get(url, params):
        # Имитируем ответ сервера с данными о новостях.
        return DummyResponse(dummy_json)

    monkeypatch.setattr(requests, "get", dummy_get)
    query = "Новости"
    result = get_weekly_news(query)
    # Проверяем, что ответ содержит либо заголовок, либо описание новости
    assert (
        "Test Article" in result or "Test description" in result
    ), "Ответ должен содержать данные о найденной новости"


def test_get_dollar_rate_error(monkeypatch):
    """
    Тестирует поведение get_dollar_rate при получении ошибочного HTTP-статуса.

    Проверяет, что функция возвращает корректное сообщение об ошибке.
    """

    def dummy_get(url):
        # Имитируем ошибочный ответ сервера (HTTP статус 500).
        return DummyResponse({}, status_code=500)

    monkeypatch.setattr(requests, "get", dummy_get)
    result = get_dollar_rate()
    assert (
        "Ошибка получения курса доллара" in result
    ), "Функция должна вернуть сообщение об ошибке при неверном статусе"


if __name__ == "__main__":
    pytest.main()
