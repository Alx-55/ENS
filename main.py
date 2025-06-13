
import asyncio
import smtplib
from email.message import EmailMessage

from fastapi import FastAPI
import httpx  # Асинхронные HTTP-запросы

app = FastAPI()

from database import engine
from models import Base

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    asyncio.create_task(weather_monitor())


# Настройки
OPENWEATHER_API_KEY = "99e09229e133cd3639c708fe595a930b"

# Индивидуальные пороги температур по каждому городу
CITY_THRESHOLDS = {
    "Kyiv": 20,
    "Krasnodar": 20
}

# Подписчики
subscribers = set()  # Список email-адресов


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

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login("olexandrhai115@gmail.com", "lftcpyhsaejlqtxk")
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


# ===== Инициализация при старте =====
@app.on_event("startup")
async def on_startup():
    asyncio.create_task(weather_monitor())


# ===== Эндпоинт подписки =====
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import SessionLocal
from models import Subscriber

async def get_db():
    async with SessionLocal() as session:
        yield session

@app.post("/subscribe")
async def subscribe(email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscriber).where(Subscriber.email == email))
    existing = result.scalar_one_or_none()

    if existing:
        return {"message": f"{email} уже подписан."}

    new_sub = Subscriber(email=email)
    db.add(new_sub)
    await db.commit()
    return {"message": f"Подписка {email} добавлена"}




# ПЕРЕКЛЮЧИЛСЯ НА DEV (на новую ветку)



