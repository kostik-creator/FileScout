from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_callback_btns(*, btns: dict[str, str], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()

def inline_actions_on_users(user):
    """Создает клавиатуру действий для администартора над пользователями."""
    return get_callback_btns(
        btns={
            'Удалить пользователя': f'delete_user_{user.phone}',
            'Изменить группу': f'change_group_{user.group_id}, {user.phone}'  
        },
        sizes=(2, 1)
    )