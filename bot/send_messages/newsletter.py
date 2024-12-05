from bot.logging.logger import bot_logger

async def send_photo_to_user(bot, chat_id, photo, caption):
    """Отправляет фото конкретному пользователю."""
    try:
        await bot.send_photo(chat_id, photo, caption=caption)
        return True
    except Exception as e:
        bot_logger.log('error', f"Не удалось отправить фото пользователю {chat_id}: {e}")
        return False

async def send_video_to_user(bot, chat_id, video, caption):
    """Отправляет видео конкретному пользователю."""
    try:
        await bot.send_video(chat_id, video, caption=caption)
        return True
    except Exception as e:
        bot_logger.log('error', f"Не удалось отправить видео пользователю {chat_id}: {e}")
        return False

async def send_message_to_user(bot, chat_id, text):
    """Отправляет текстовое сообщение конкретному пользователю."""
    try:
        await bot.send_message(chat_id, text)
        return True
    except Exception as e:
        bot_logger.log('error', f"Не удалось отправить сообщение пользователю {chat_id}: {e}")
        return False
