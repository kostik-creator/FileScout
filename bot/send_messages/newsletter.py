from bot.logging.logger import bot_logger


async def send_photo_to_user(bot, chat_id, photo, caption):
    """Отправляет фото конкретному пользователю.

    Args:
        bot: Экземпляр бота, используемый для отправки сообщения.
        chat_id (int): ID чата пользователя, которому отправляется фото.
        photo (str): ID или URL фото, которое нужно отправить.
        caption (str): Подпись к фото.

    Returns:
        bool: True, если фото успешно отправлено, иначе False.
    """
    try:
        await bot.send_photo(chat_id, photo, caption=caption)
        return True
    except Exception as e:
        bot_logger.log('error', f"Не удалось отправить фото пользователю {chat_id}: {e}")
        return False

async def send_video_to_user(bot, chat_id, video, caption):
    """Отправляет видео конкретному пользователю.

    Args:
        bot: Экземпляр бота, используемый для отправки сообщения.
        chat_id (int): ID чата пользователя, которому отправляется видео.
        video (str): ID или URL видео, которое нужно отправить.
        caption (str): Подпись к видео.

    Returns:
        bool: True, если видео успешно отправлено, иначе False.
    """
    try:
        await bot.send_video(chat_id, video, caption=caption)
        return True
    except Exception as e:
        bot_logger.log('error', f"Не удалось отправить видео пользователю {chat_id}: {e}")
        return False

async def send_message_to_user(bot, chat_id, text):
    """Отправляет текстовое сообщение конкретному пользователю.

    Args:
        bot: Экземпляр бота, используемый для отправки сообщения.
        chat_id (int): ID чата пользователя, которому отправляется сообщение.
        text (str): Текст сообщения, которое нужно отправить.

    Returns:
        bool: True, если сообщение успешно отправлено, иначе False.
    """
    try:
        await bot.send_message(chat_id, text)
        return True
    except Exception as e:
        bot_logger.log('error', f"Не удалось отправить сообщение пользователю {chat_id}: {e}")
        return False