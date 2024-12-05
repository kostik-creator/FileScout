from typing import List, Optional, Dict

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.logging.logger import sqlalchemy_logger
from bot.database.models import Admin, Group, User

############### Работа с группами ###############

async def orm_create_groups(session: AsyncSession, categories: List[str]) -> None:
    """Создает группы в базе данных, если они еще не существуют.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        categories (List[str]): Список названий групп для создания.
    """
    try:
        query = select(Group)
        result = await session.execute(query)
        if result.first():
            return
        session.add_all([Group(name=name) for name in categories]) 
        await session.commit()
    except Exception as e:
        sqlalchemy_logger.log('error', f"Ошибка при создании групп: {e}")

async def get_groups(session: AsyncSession) -> List[Group]:
    """Получает список всех групп.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        List[Group]: Список объектов Group.
    """
    try:
        result = await session.execute(select(Group))
        return result.scalars().all()
    except Exception as e:
        sqlalchemy_logger.log('error', f"Ошибка при получении групп: {e}")
        return []

async def get_group_by_id(session: AsyncSession, group_id: int) -> Optional[Group]:
    """Получает группу по ее ID.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        group_id (int): ID группы для получения.

    Returns:
        Optional[Group]: Объект группы, если найден, иначе None.
    """
    try:
        group = await session.get(Group, group_id)
        return group.name if group else None
    except Exception as e:
        sqlalchemy_logger.log('error', f"Ошибка при получении группы по ID {group_id}: {e}")
        return None

############### Работа с админами ###############

async def orm_create_first_admin(session: AsyncSession, superadmin: Dict[str, str]) -> None:
    """Создает первого администратора, если он еще не существует.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        superadmin (Dict[str, str]): Словарь с информацией о суперадминистраторе (телефон и пароль).
    """
    try:
        query = select(Admin)
        result = await session.execute(query)
        if result.first():
            return
        session.add(Admin(phone=superadmin['phone'], password=superadmin['password']))
        await session.commit()
    except Exception as e:
        sqlalchemy_logger.log('error', f"Ошибка при создании первого администратора: {e}")

async def orm_get_admin(session: AsyncSession, phone: str) -> Optional[Admin]:
    """Получает администратора по номеру телефона.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        phone (str): Номер телефона администратора.

    Returns:
        Optional[Admin]: Объект администратора, если найден, иначе None.
    """
    try:
        query = select(Admin).where(Admin.phone == phone)
        result = await session.execute(query)
        admin = result.scalar_one_or_none()
        return admin
    except Exception as e:
        sqlalchemy_logger.log('error', f"Ошибка при получении администратора по телефону {phone}: {e}")
        return None

async def orm_add_administrator(session: AsyncSession, phone_number: str, password: str) -> None:
    """Добавляет нового администратора в базу данных.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        phone_number (str): Номер телефона нового администратора.
        password (str): Пароль нового администратора.
    """
    try:
        new_admin = Admin(phone=phone_number, password=password)
        session.add(new_admin)    
        await session.commit()
    except Exception as e:
        sqlalchemy_logger.log('error', f"Ошибка при добавлении администратора с номером {phone_number}: {e}")

############### Работа с пользователями ###############

async def orm_get_user(session: AsyncSession, phone: str) -> Optional[User]:
    """Получает пользователя по номеру телефона из базы данных.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        phone (str): Номер телефона пользователя.

    Returns:
        Optional[User]: Объект пользователя, если найден, иначе None.
    """
    try:
        query = select(User).where(User.phone == phone)
        result = await session.execute(query)
        user = result.scalar_one_or_none()  
        return user
    except Exception as e:
        sqlalchemy_logger.log('error', f"Ошибка при получении пользователя по телефону {phone}: {e}")
        return None

async def orm_add_user(session: AsyncSession, phone_number: str, password: str, group_id: int) -> None:
    """Добавляет нового пользователя в базу данных.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        phone_number (str): Номер телефона нового пользователя.
        password (str): Пароль нового пользователя.
        group_id (int): ID группы, к которой будет принадлежать пользователь.
    """
    try:
        new_user = User(phone=phone_number, password=password, group_id=group_id)
        session.add(new_user)
        await session.commit()
    except Exception as e:
        sqlalchemy_logger.log('error', f"Ошибка при добавлении пользователя с номером {phone_number}: {e}")

async def orm_get_all_users(session: AsyncSession) -> List[User]:
    """Получает всех пользователей вместе с их группами.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        List[User]: Список объектов User.
    """
    try:
        query = select(User).options(selectinload(User.group))
        result = await session.execute(query)
        return result.scalars().all()
    except Exception as e:
        sqlalchemy_logger.log('error', f"Ошибка при получении всех пользователей: {e}")
        return []

async def orm_delete_user(session: AsyncSession, user: User) -> None:
    """Удаляет пользователя из базы данных.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        user (User): Объект пользователя для удаления.
    
    Raises:
        ValueError: Если пользователь не найден.
    """
    try:
        # Проверка, существует ли пользователь
        if user is None:
            raise ValueError("Пользователь не найден для удаления.")

        await session.delete(user)  # Удаляем пользователя
        await session.commit()  # Коммитим изменения
    except Exception as e:
        sqlalchemy_logger.log('error', f"Ошибка при удалении пользователя: {e}")

async def orm_get_users_by_group(session: AsyncSession, group_id: int):
    """Получает всех пользователей, принадлежащих к указанной группе.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        group_id (int): Идентификатор группы, для которой необходимо получить пользователей.

    Returns:
        List[User]: Список пользователей, принадлежащих к указанной группе. 
                     Если произошла ошибка, возвращает пустой список.
    """
    try:
        result = await session.execute(select(User).where(User.group_id == group_id))
        users = result.scalars().all() 
        return users
    except Exception as e:
        sqlalchemy_logger.log('error', f"Ошибка при получении пользователей группы {group_id}: {e}")
        return []

async def orm_add_chatid_for_user(session: AsyncSession, chat_id: int, phone: str):
    """Обновляет chat_id для пользователя по номеру телефона.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        chat_id (int): Идентификатор чата, который необходимо обновить.
        phone (str): Номер телефона пользователя, для которого нужно обновить chat_id.

    Returns:
        bool: True, если обновление прошло успешно; False, если пользователь не найден или произошла ошибка.
    """
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
    """Получает chat_id пользователя по номеру телефона.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        phone (str): Номер телефона пользователя, для которого нужно получить chat_id.

    Returns:
        int or None: chat_id пользователя, если он найден; None, если произошла ошибка или пользователь не найден.
    """
    try:
        result = await session.execute(
            select(User.chat_id).where(User.phone == phone)
        )
        chat_id = result.scalar() 
        return chat_id
    except Exception as e:
        sqlalchemy_logger.log('error', f"Ошибка при получении chat_id для пользователя с номером {phone}: {e}")
        return None