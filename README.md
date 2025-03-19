# Chat with ChatGPT 🤖

![Демонстрация работы](./preview.gif)

## Установка и запуск
  

1. Клонируйте репозиторий:
   ```bash
   git clone git@github.com:voidCaloneian/ChatGPT_Chat_With_Functions.git
   cd ChatGPT_Chat_With_Functions
   ```

### Установка

- Через **Docker**:
   
   Билд и запуск проекта
   ```bash
   docker build -t mcp_chatgpt . 
   docker run -d --name mcp_chatgpt -p 8000:8000 mcp_chatgpt
   ```
   Опциональный запуск тестов и репорт покрытия
   ```bash
   docker exec mcp_chatgpt coverage run --source=app -m pytest && coverage report
   ```
> [!WARNING]
> **Не забудьте указать свой OpenAI API ключ в **.env** файле!**

- Напрямую

1. Создайте виртуальное окружение:
   ```bash
   python3 -m venv env
   source env/bin/activate # Windows: env\Scripts\activate
   pip install -r requirements.txt
2. Укажите ваш **OpenAI** API ключ в **.env** файле
   > **Остальные ключи я уже указал** 
   
3. Запустите сервер:
   ```bash
   hypercorn main:app --bind 0.0.0.0:8000
   ```
4. Опциональный запуск тестов 
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
> 
> **А также!** Все функции обрабатываются асинхронно, поэтому даже если мы попросим узнать погоду о 10 разных городах, то он выполнит все эти функции почти также быстро, как это было бы для 1 функции.


- Модель обрабатывает сообщения и, если необходимо, совершает вызовы функций:
  - **get_weather** для получения погоды в указанном городе.
  - **get_dollar_rate** для получения курса обмена USD к RUB.
  - **get_weekly_news** для получения новостей по заданной теме.
- Вы можете отправлять запросы с несколькими вопросами сразу. Например:
> [!Note]
> 
> **Попробуйте отправить комплексное сообщение! Будут вызваны сразу все требуемые функции!**
> ```
> Какой курс доллара и погода в Москве и Санкт-Петербурге, 
> И в 5 случайных городах США, и 7 городах Европы,
> А также мне было бы интересно узнать новости про программирование,
> Да и вообще про актуальные мировые события!
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

