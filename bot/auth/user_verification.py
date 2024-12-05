from aiogram import types
from aiogram.fsm.context import FSMContext


from bot.auth.auth_function import check_password
from bot.keyboards.reply import get_keyboard
from bot.logging.logger import bot_logger

from typing import Any

INITIAL_ADMIN_KB = get_keyboard(
    "Поиск",
    "❌ Выйти",
    "Админ панель",
    sizes=(2, 1)
)

USER_KB = get_keyboard(
    "Поиск", 
    "❌ Выйти", 
    placeholder="Что вас интересует?"
)

async def check_admin_credentials(admin: Any, password: str, message: types.Message) -> bool:
    """Проверяет учетные данные администратора.

    Args:
        admin (Any): Объект администратора, полученный из БД.
        password (str): Введенный пароль администратора.
        message (types.Message): Объект message.

    Returns:
        bool: True, если учетные данные верны, иначе False.
    """
    if admin:
        stored_hashed_password = admin.password
        if check_password(password, stored_hashed_password):
            await message.answer(
                "🎉 Добро пожаловать, администратор! 🌟\n\n"
                "Теперь у вас есть доступ ко всем функциям управления системой. "
                "Вы можете управлять пользователями и настраивать параметры.\n\n"
                "Нажмите на кнопку ниже, чтобы начать то действие, которое вам требуется:\n",
                reply_markup=INITIAL_ADMIN_KB
            )
            bot_logger.log('info', f'Администратор {message.from_user.username} успешно вошел в аккаунт.')
            return True
    return False

async def check_user_credentials(user: Any, password: str, message: types.Message) -> bool:
    """Проверяет учетные данные обычного пользователя.

    Args:
        user (Any): Объект пользователя, полученный из БД.
        password (str): Введенный пароль пользователя.
        message (types.Message): Объект message.

    Returns:
        bool: True, если учетные данные верны, иначе False.
    """
    if user:
        stored_hashed_password = user.password  
        if check_password(password, stored_hashed_password):
            await message.answer(
                "🎉 Добро пожаловать! 🌈\n\n"
                "Теперь вы можете легко искать файлы в системе. "
                "Просто нажмите кнопку Поиск, чтобы начать!\n\n",
                reply_markup=USER_KB
            )
            bot_logger.log('info', f'Пользователь {message.from_user.username} успешно вошел в аккаунт.')
            
            return True
    return False

async def get_variable_admin(state: FSMContext):
    """Получает данные пользователя из состояния и проверяет, является ли он администратором."""
    user_data = await state.get_data()
    is_admin = user_data.get('admin', False)  # По умолчанию False, если ключ отсутствует
    return is_admin