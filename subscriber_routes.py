# ====== subscriber_routes.py ======
# Этот файл содержит все маршруты, связанные с подпиской
# и работает отдельно от основного main.py, чтобы разделить ответственность.
# ===== Комментарии проекта сохранены без изменений =====

from fastapi import APIRouter, Form, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Subscriber
from database import SessionLocal
from starlette.templating import Jinja2Templates

router = APIRouter()

# Эта строка говорит FastAPI о том, что все шаблоны будут находиться в папке tamplates
templates = Jinja2Templates(directory="templates")

# ===== Получение сессии базы данных =====


async def get_db():
    async with SessionLocal() as session:
        yield session


# ==== Эндпоинд отвечающий за главную (домашнюю) страницу моего сайта. Пользователь открывает сайт в брузере (http://localhost:8000/),
# ==== при этом вызывается эта функция. При выполнении этого запроса в 'docs' по сути я получаю HTML-страницу (Home Page):
# ==== при тестовом "замораживании" этого эндпоинда, приложением пользоваться можно, но функционал реализовывать можно в 'docs' (Home Page отсутствует)
@router.get("/", response_class=HTMLResponse)
async def form_page(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscriber))  # этими строками получаем всех подписчиков
    subscribers = result.scalars().all()           # из таблицы subscribers из БД.

    return templates.TemplateResponse("index.html", {"request": request, "subscribers": subscribers})  # этой строкой передаются данные из этого
                                                                                                       # файла на страницу-HTML (в index.html).


@router.post("/subscribe_form")  # работает на HTML-странице (подписка)
async def subscribe_form(email: str = Form(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscriber).where(Subscriber.email == email))
    existing = result.scalar_one_or_none()

    if not existing:
        db.add(Subscriber(email=email))
        await db.commit()
    return RedirectResponse("/", status_code=303)


@router.post("/unsubscribe_form")  # работает на HTML-странице (отписка)
async def unsubscribe_form(email: str = Form(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscriber).where(Subscriber.email == email))
    subscriber = result.scalar_one_or_none()

    if subscriber:
        await db.delete(subscriber)
        await db.commit()
    return RedirectResponse("/", status_code=303)


# ===== Эндпоинт подписки =====
@router.post("/subscribe")  # работает в API/Swagger (подписка)
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
@router.delete("/unsubscribe")  # работает в API/Swagger (отписка)
async def unsubscribe(email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscriber).where(Subscriber.email == email))
    subscriber = result.scalar_one_or_none()

    if not subscriber:
        return {"message": f"Подписчик с email {email} не найден."}

    await db.delete(subscriber)
    await db.commit()
    return {"message": f"Подписка {email} удалена."}
