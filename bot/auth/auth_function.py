import random
import string
import bcrypt

from aiogram.fsm.context import FSMContext

from typing import Tuple

async def get_auth_data(state: FSMContext) -> Tuple[str, str]:
    """Получает номер телефона и пароль пользователя из состояния.

    Args:
        state (FSMContext): Состояние машины состояний.

    Returns:
        Tuple[str, str]: Кортеж, содержащий номер телефона и пароль пользователя.
    """
    user_data = await state.get_data()
    phone_number = user_data.get('phone_number')
    password = user_data.get('password')
    return phone_number, password

def hash_password(password: str) -> str:
    """Хеширует пароль и возвращает его в виде строки.

    Args:
        password (str): Пароль, который необходимо хешировать.

    Returns:
        str: Хешированный пароль в виде строки.
    """
    pwd_bytes = password.encode('utf-8')
    hashed_password = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt())
    return hashed_password.decode('utf-8')

def check_password(plain_password: str, hashed_password: str) -> bool:
    """Сравнивает введенный пароль с сохраненным хешем.

    Args:
        plain_password (str): Введенный пользователем пароль.
        hashed_password (str): Хешированный пароль для сравнения.

    Returns:
        bool: True, если пароли совпадают, иначе False.
    """
    plain_password_bytes = plain_password.encode('utf-8')
    return bcrypt.checkpw(plain_password_bytes, hashed_password.encode('utf-8'))

def generate_hashed_password(length: int = 8) -> Tuple[str, str]:
    """Генерирует случайный пароль и возвращает его хеш.

    Args:
        length (int): Длина генерируемого пароля (по умолчанию 8).

    Returns:
        Tuple[str, str]: Кортеж, содержащий сгенерированный пароль и его хеш.
    """
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    return password, hashed_password