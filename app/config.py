import os

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

DOLLAR_API_KEY = os.getenv("DOLLAR_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([DOLLAR_API_KEY, WEATHER_API_KEY, NEWS_API_KEY, OPENAI_API_KEY]):
    raise ValueError("Один или несколько API ключей не найдены в переменных окружения.")

WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
DOLLAR_API_URL = f"https://v6.exchangerate-api.com/v6/{DOLLAR_API_KEY}/latest/USD"
NEWS_API_URL = "https://newsapi.org/v2/everything"

# Роли сообщений
USER = "user"
ASSISTANT = "assistant"
TOOL = "tool"
