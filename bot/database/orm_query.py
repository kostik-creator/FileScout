from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict
from bot.logging.logger import sqlalchemy_logger
from bot.database.models import Admin, Group, User

############### Работа с группами ###############

async def orm_create_groups(session: AsyncSession, categories: List[str]) -> None:
    """Создает группы в базе данных, если они еще не существуют.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        categories (List[str]): Список названий групп для создания.
    """
    query = select(Group)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Group(name=name) for name in categories]) 
    await session.commit()

async def get_groups(session: AsyncSession) -> List[Group]:
    """Получает список всех групп.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        List[Group]: Список объектов Group.
    """
    result = await session.execute(select(Group))
    return result.scalars().all()

async def get_group_by_id(session: AsyncSession, group_id: int) -> Optional[Group]:
    """Получает группу по ее ID.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        group_id (int): ID группы для получения.

    Returns:
        Optional[Group]: Объект группы, если найден, иначе None.
    """
    group_id = int(group_id) 
    group = await session.get(Group, group_id)
    return group.name if group else None
    

############### Работа с админами ###############

async def orm_create_first_admin(session: AsyncSession, superadmin: Dict[str, str]) -> None:
    """Создает первого администратора, если он еще не существует.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        superadmin (Dict[str, str]): Словарь с информацией о суперадминистраторе (телефон и пароль).
    """
    query = select(Admin)
    result = await session.execute(query)
    if result.first():
        return
    session.add(Admin(phone=superadmin['phone'], password=superadmin['password']))
    await session.commit()

async def orm_get_admin(session: AsyncSession, phone: str) -> Optional[Admin]:
    """Получает администратора по номеру телефона.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        phone (str): Номер телефона администратора.

    Returns:
        Optional[Admin]: Объект администратора, если найден, иначе None.
    """
    query = select(Admin).where(Admin.phone == phone)
    result = await session.execute(query)
    admin = result.scalar_one_or_none()
    return admin

async def orm_add_administrator(session: AsyncSession, phone_number: str, password: str) -> None:
    """Добавляет нового администратора в базу данных.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        phone_number (str): Номер телефона нового администратора.
        password (str): Пароль нового администратора.
    """
    new_admin = Admin(phone=phone_number, password=password)
    session.add(new_admin)    
    await session.commit()

############### Работа с пользователями ###############

async def orm_get_user(session: AsyncSession, phone: str) -> Optional[User]:
    """Получает пользователя по номеру телефона из базы данных.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        phone (str): Номер телефона пользователя.

    Returns:
        Optional[User]: Объект пользователя, если найден, иначе None.
    """
    query = select(User).where(User.phone == phone)
    result = await session.execute(query)
    user = result.scalar_one_or_none()  
    return user

async def orm_add_user(session: AsyncSession, phone_number: str, password: str, group_id: int) -> None:
    """Добавляет нового пользователя в базу данных.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        phone_number (str): Номер телефона нового пользователя.
        password (str): Пароль нового пользователя.
        group_id (int): ID группы, к которой будет принадлежать пользователь.
    """
    new_user = User(phone=phone_number, password=password, group_id=group_id)
    session.add(new_user)
    await session.commit()

async def orm_get_all_users(session: AsyncSession) -> List[User]:
    """Получает всех пользователей вместе с их группами.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        List[User]: Список объектов User.
    """
    query = select(User).options(selectinload(User.group))
    result = await session.execute(query)
    return result.scalars().all()
async def orm_delete_user(session: AsyncSession, user: User) -> None:
    """Удаляет пользователя из базы данных.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        user (User): Объект пользователя для удаления.
    
    Raises:
        ValueError: Если пользователь не найден.
    """
    # Проверка, существует ли пользователь
    if user is None:
        raise ValueError("Пользователь не найден для удаления.")

    await session.delete(user)  # Удаляем пользователя
    await session.commit()  # Коммитим изменения

async def orm_get_users_by_group(session: AsyncSession, group_id: int):
    """Получает всех пользователей, принадлежащих к указанной группе."""
    try:
        result = await session.execute(select(User).where(User.group_id == group_id))
        users = result.scalars().all() 
        return users
    except Exception as e:
        # Логируем ошибку
        sqlalchemy_logger.log('error', f"Ошибка при получении пользователей группы {group_id}: {e}")
        return []

async def orm_add_chatid_for_user(session: AsyncSession, chat_id: int, phone: str):
    """Обновляет chat_id для пользователя по номеру телефона."""
    try:
        statement = (
            update(User)
            .where(User.phone == phone)
            .values(chat_id=chat_id)
        )
        result = await session.execute(statement)
        await session.commit()  

        if result.rowcount == 0:
            return False

        return True  
    except Exception as e:
        sqlalchemy_logger.log('error', f"Ошибка при обновлении chat_id для пользователя с номером {phone}: {e}")
        return False
    
async def orm_get_chatid_by_phone(session: AsyncSession, phone: str):
    """Получает chat_id пользователя по номеру телефона."""
    try:
        result = await session.execute(
            select(User.chat_id).where(User.phone == phone)
        )
        chat_id = result.scalar() 

        return chat_id
    except Exception as e:
        sqlalchemy_logger.log('error', f"Ошибка при получении chat_id для пользователя с номером {phone}: {e}")
        return None  