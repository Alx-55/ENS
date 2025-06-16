
import asyncio  # обеспечивает асинхронность
import smtplib
from email.message import EmailMessage

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

import httpx  # Асинхронные HTTP-запросы
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from starlette.templating import Jinja2Templates  # Шаблонизатор - элемент, обеспечивает связь между содержимым папки tamplates и
                                                  # главным файлом проекта. Связующее звено между Python-кодом и HTML-шаблонами
from database import engine, SessionLocal
from models import Base, Subscriber

templates = Jinja2Templates(directory="templates")  # Эта строка говорит FastAPI о том, что все шаблоны будут находиться в папке tamplates

app = FastAPI()


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


# ===== Получение сессии базы данных =====
async def get_db():
    async with SessionLocal() as session:
        yield session


# ==== Эндпоинд отвечающий за главную (домашнюю) страницу моего сайта. Пользователь открывает сайт в брузере (http://localhost:8000/),
# ==== при этом вызывается эта функция. При выполнении этого запроса в 'docs' по сути я получаю HTML-страницу (Home Page):

@app.get("/", response_class=HTMLResponse)
async def form_page(request: Request, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Subscriber))  # этими строками получаем всех подписчиков
    subscribers = result.scalars().all()           # из таблицы subscribers из БД.

    return templates.TemplateResponse("index.html", {"request": request, "subscribers": subscribers})  # этой строкой передаются данные из
                                                                                                # файла main.py на страницу-HTML (в index.html).


@app.post("/subscribe_form")  # работает на HTML-странице (подписка)
async def subscribe_form(email: str = Form(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscriber).where(Subscriber.email == email))
    existing = result.scalar_one_or_none()

    if not existing:
        db.add(Subscriber(email=email))
        await db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/unsubscribe_form")  # работает на HTML-странице (отписка)
async def unsubscribe_form(email: str = Form(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscriber).where(Subscriber.email == email))
    subscriber = result.scalar_one_or_none()

    if subscriber:
        await db.delete(subscriber)
        await db.commit()
    return RedirectResponse("/", status_code=303)


# ===== Эндпоинт подписки =====
@app.post("/subscribe")  # работает в API/Swagger (подписка)
async def subscribe(email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscriber).where(Subscriber.email == email))
    existing = result.scalar_one_or_none()

    if existing:
        return {"message": f"{email} уже подписан."}

    new_sub = Subscriber(email=email)
    db.add(new_sub)
    await db.commit()
    return {"message": f"Подписка {email} добавлена"}


# ===== Эндпоинт отписки =====
@app.delete("/unsubscribe")  # работает в API/Swagger (отписка)
async def unsubscribe(email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscriber).where(Subscriber.email == email))
    subscriber = result.scalar_one_or_none()

    if not subscriber:
        return {"message": f"Подписчик с email {email} не найден."}

    await db.delete(subscriber)
    await db.commit()
    return {"message": f"Подписка {email} удалена."}

