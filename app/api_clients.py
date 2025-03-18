import requests
from loguru import logger

from app.config import (
    WEATHER_API_URL,
    WEATHER_API_KEY,
    DOLLAR_API_URL,
    NEWS_API_URL,
    NEWS_API_KEY,
)


def get_weather(location: str) -> str:
    """
    Получает текущую погоду для указанного местоположения.

    :param location: Название местоположения (город).
    :return: Строка с описанием погоды и температурой.
    """
    try:
        params = {"q": location, "appid": WEATHER_API_KEY, "units": "metric"}
        response = requests.get(WEATHER_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        desc: str = data.get("weather", [{}])[0].get("description", "нет данных")
        temp: Union[float, str] = data.get("main", {}).get("temp", "нет данных")
        return f"Погода в {location}: {desc}, температура {temp}°C"
    except Exception as e:
        logger.error("Ошибка получения погоды: {}", e)
        return "Ошибка получения данных о погоде."


def get_dollar_rate() -> str:
    """
    Получает текущий курс доллара.

    :return: Строка с информацией о курсе обмена USD к RUB.
    """
    try:
        response = requests.get(DOLLAR_API_URL)
        response.raise_for_status()
        data = response.json()
        rates = data.get("conversion_rates", {})
        return f"Курсы: {rates}" if rates else "Данные о курсе недоступны."
    except Exception as e:
        logger.error("Ошибка получения курса доллара: {}", e)
        return "Ошибка получения курса доллара."


def get_weekly_news(query: str = "Новости") -> str:
    """
    Получает новости за последнюю неделю по указанной теме.

    :param query: Тема новостей (по умолчанию "Новости").
    :return: Строка с последними новостными заголовками.
    """
    try:
        params = {"q": query, "apiKey": NEWS_API_KEY, "pageSize": 5}
        response = requests.get(NEWS_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])
        if articles:
            headlines = [article.get("title", "Без заголовка") for article in articles]
            return "Последние новости: " + "; ".join(headlines)
        else:
            return "Новостные данные недоступны."
    except Exception as e:
        logger.error("Ошибка получения новостей: {}", e)
        return "Ошибка получения новостей."
