# Chat with ChatGPT 🤖

![Демонстрация работы](./preview.gif)

## Установка и запуск

1. Клонируйте репозиторий:
   ```bash
   git clone git@github.com:voidCaloneian/ChatGPT_Chat_With_Functions.git
   cd ChatGPT_Chat_With_Functions
   ```
2. Создайте виртуальное окружение:
   ```bash
   python3 -m venv env
   source env/bin/activate # Windows: env\Scripts\activate
   pip install -r requirements.txt
3. Укажите ваш **OpenAI** API ключ в .env файле
   > **Остальные ключи я уже указал** 
   
4. Запустите сервер:
   ```bash
   hypercorn main:app --bind 0.0.0.0:8000
   ```
5. Опциональный запуск тестов 
   ```bash
   coverage run --source=app -m pytest && coverage report
   ```
> [!Note] 
> Поздравляю, сервер запущен!
> Заходите на ```localhost:8000/``` и тестируйте

## О работе приложения

Приложение использует FastAPI с WebSocket для чата в режиме реального времени ChatGPT, который может вызывать различные инструменты.
> [!IMPORTANT]
> **Дополнительно** я **реализовал стриминг сообщений** по мере их генерации. Как на бэкенде, так и на фронтенде. Это значит, что сообщение будет отправляться почанково, как только модель их генерирует. Это позволяет клиенту не ждать, пока весь модель сгенерирует полный ответ.


- Модель обрабатывает сообщения и, если необходимо, совершает вызовы функций:
  - **get_weather** для получения погоды в указанном городе.
  - **get_dollar_rate** для получения курса обмена USD к RUB.
  - **get_weekly_news** для получения новостей по заданной теме.
- Вы можете отправлять запросы с несколькими вопросами сразу. Например:
> [!Note]
> 
> **Попробуйте отправить комплексное сообщение! Будут вызваны сразу все требуемые функции!**
> ```
> Какой курс доллара и погода в Москве и Санкт-Петербурге, и в 2 случайных городах США,
> а также мне было бы интересно узнать новости про программирование,
> да и вообще про актуальные мировые события!
> ```
  
  При получении такого запроса модель выполнит вызовы сразу нескольких инструментов и объединит результаты в ответе!

> [!NOTE]
> Я не реализовывал сжатие сообщений, поэтому если количество токенов будет превышено, то возникнет ошибка. В таком случае просто обновите страницу.
>
> Используется **GPT-4o**. Хотя если требовалось бы сделать его поумнее, то предпочтительнее было бы использовать **o3-mini**, но выбрал **GPT-4o**, так как он быстрее и для презентации проекта идеально подходит
> 
> История сообщений привязана к вебсокету. То есть, у каждого открытого окна сайта своя история сообщений. Когда закрывается вебсокет, очищается история сообщений по нему.

> [!WARNING]
   Жду фидбек!

