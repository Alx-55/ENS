
# Подключение к PostGreSQL через SQLAlchemy (в асинхронном режиме), а также создание сессии для работы с БД:

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://weather_user:password123@localhost/weather_db"  # строка подключения к БД

engine = create_async_engine(DATABASE_URL, echo=True)  # engine - асинхронный движок SQLAlchemy
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)  # SessionLocal - фабрика сессий для работы с БД
                                                                   # (используется через Depends() в main.py)


class Base(DeclarativeBase):  # Base — базовый класс для моделей (все таблицы наследуются от него)
    pass

