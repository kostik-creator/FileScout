import bcrypt
from aiogram import types
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from bot.auth.auth_function import get_auth_data
from bot.auth.auth_function import check_password
from bot.database.orm_query import orm_get_admin


class IsAdmin(Filter):
    def __init__(self) -> None:
        pass
    
    async def __call__(self, message: types.Message, state: FSMContext, session: AsyncSession) -> bool:
        
        phone_number, password = await get_auth_data(state)  

        if not phone_number or not password:
            return False 

        admin = await orm_get_admin(session, phone_number)  
        
        if admin is None:
            return False  
        
        stored_hashed_password = admin.password  

        if check_password(password, stored_hashed_password):
            return True  
        
        return False