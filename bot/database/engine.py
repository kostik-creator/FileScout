import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.database.models import Base
from bot.logging.logger import bot_logger
from bot.database.orm_query import orm_create_groups, orm_create_first_admin
from bot.common.texts_for_db import groups, superadmin

from dotenv import load_dotenv

load_dotenv('.env')

DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_HOST = os.getenv('POSTGRES_HOST')
DB_PORT = os.getenv('POSTGRES_PORT')
DB_NAME = os.getenv('POSTGRES_DB')

engine = create_async_engine(
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    echo=True
)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def create_db() -> None:
    """Создает базу данных и инициализирует её начальными данными.

    Эта функция создает все таблицы в базе данных, используя метаданные класса Base,
    а также добавляет группы и первого администратора, если они еще не существуют.

    Returns:
        None
    """
    async with engine.begin() as conn:
        bot_logger.log('info', 'База данных успешно создана')
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:    
        await orm_create_groups(session, groups)
        await orm_create_first_admin(session, superadmin)

async def drop_db() -> None:
    """Удаляет все таблицы из базы данных.

    Эта функция сбрасывает базу данных, удаляя все существующие таблицы.

    Returns:
        None
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)