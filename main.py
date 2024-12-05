import os
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.mongo import MongoStorage

from bot.middleware.db import DataBaseSession
from bot.database.engine import create_db, session_maker
from bot.logging.logger import bot_logger
from bot.handlers.user_handlers import user_router
from bot.handlers.admin_handlers import admin_router
from bot.mongodb.mongo_config import mongo_db

from dotenv import load_dotenv

load_dotenv('.env')


bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

storage = MongoStorage(db_name=mongo_db.db_name, client=mongo_db.client)

dp = Dispatcher(storage=storage)
dp.include_routers(user_router, admin_router)


async def on_startup(bot):  
    bot_logger.log('info', 'База данных успешно создана')

    await create_db()

async def on_shutdown(bot):
    bot_logger.log('info', 'Бот лег ')

async def main():
    dp.startup.register(on_startup) 
    dp.shutdown.register(on_shutdown)
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":  
    asyncio.run(main()) 