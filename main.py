
import asyncio  # обеспечивает асинхронность
import smtplib
from email.message import EmailMessage
from fastapi import FastAPI, Request, Form, Depends
import httpx  # Асинхронные HTTP-запросы
from sqlalchemy import select
from starlette.templating import Jinja2Templates  # Шаблонизатор - элемент, обеспечивает связь между содержимым папки tamplates и
                                                  # главным файлом проекта. Связующее звено между Python-кодом и HTML-шаблонами
from database import engine, SessionLocal
from models import Base, Subscriber
from subscriber_routes import router as subscriber_router  # это связка с файлом "подписки" subscriber_routes.py


templates = Jinja2Templates(directory="templates")  # Эта строка говорит FastAPI о том, что все шаблоны будут находиться в папке tamplates


app = FastAPI()

app.include_router(subscriber_router)  # !! что интересно, это строка должна быть ниже по коду чем строка app = FastAPI()
                                       # Эта строка подключает маршруты (endpoints) из файла subscriber_routes к основному Fast-приложению.

# ===== Создание таблиц и запуск мониторинга =====


@app.on_event("startup")  # Инициализация БД при старте
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    asyncio.create_task(weather_monitor())


# Настройки
OPENWEATHER_API_KEY = "99e09229e133cd3639c708fe595a930b"

# Индивидуальные пороги температур по каждому городу
CITY_THRESHOLDS = {
    "Kyiv": 20,
    "Krasnodar": 25
}


# ===== Получение температуры из OpenWeather =====
async def get_temperature(city: str):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        return data["main"]["temp"]


# ===== Отправка email-уведомлений =====
async def send_notifications(city: str, temp: float):
    async with SessionLocal() as db:
        result = await db.execute(select(Subscriber))
        subscribers = result.scalars().all()

    if not subscribers:
        print("Нет подписчиков — уведомление не отправлено.")
        return

    emails = [s.email for s in subscribers]

    msg = EmailMessage()
    msg.set_content(f"⚠️ Внимание! В городе {city} температура {temp}°C — жарко!")
    msg["Subject"] = f"Жаркая погода в {city}"
    msg["From"] = "olexandrhai115@gmail.com"
    msg["To"] = ", ".join(emails)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:  # smtplib.SMTP_SSL("smtp.gmail.com", 465) - это вход на сервер Google
        smtp.login("olexandrhai115@gmail.com", "lftcpyhsaejlqtxk")  # пароль приложения; этой строкой я авторизуюсь
        smtp.send_message(msg)


# ===== Мониторинг погоды по городам =====
async def weather_monitor():
    while True:
        for city, threshold in CITY_THRESHOLDS.items():
            try:
                temp = await get_temperature(city)
                print(f"{city}: {temp}°C (порог: {threshold}°C)")
                if temp > threshold:
                    await send_notifications(city, temp)
            except Exception as e:
                print(f"Ошибка при получении температуры для {city}: {e}")
        await asyncio.sleep(600)  # проверка каждые 10 минут

