
import httpx

OPENWEATHER_API_KEY = "99e09229e133cd3639c708fe595a930b"


async def get_temperature(city: str):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        return data["main"]["temp"]

HOT_THRESHOLD = 15

from fastapi import FastAPI
import asyncio

app = FastAPI()

subscribers = set()  # допустим, список email или token для уведомлений


@app.on_event("startup")
async def start_weather_monitor():
    asyncio.create_task(weather_monitor())


async def weather_monitor():
    while True:
        temp = await get_temperature("Kyiv")
        if temp > HOT_THRESHOLD:
            await send_notifications(temp)
        await asyncio.sleep(600)  # каждые 10 минут

import smtplib
from email.message import EmailMessage


async def send_notifications(temp):
    if not subscribers:
        print("Нет подписчиков — уведомление не отправлено.")
        return
    msg = EmailMessage()
    msg.set_content(f"Внимание! Температура сейчас {temp}°C. Жарко!")
    msg["Subject"] = "Жаркая погода"
    msg["From"] = "your@email.com"
    msg["To"] = ", ".join(subscribers)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login("olexandrhai115@gmail.com", "lftcpyhsaejlqtxk")  # Generated app password; Your app password for your device
        smtp.send_message(msg)                                                   # lftc pyhs aejl qtxk       (Google сгенерировал 16-значный пароль)


@app.post("/subscribe")
async def subscribe(email: str):
    subscribers.add(email)
    return {"message": f"Подписка {email} добавлена"}





