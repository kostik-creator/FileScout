from aiogram import F, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy.ext.asyncio import AsyncSession


from bot.auth.auth_function import generate_hashed_password
from bot.filters.isadmin import IsAdmin
from bot.keyboards.reply import get_keyboard
from bot.logging.logger import bot_logger
from bot.database.orm_query import (
    get_group_by_id,
    get_groups,
    orm_add_administrator,
    orm_add_user,
    orm_delete_admin,
    orm_delete_user,
    orm_get_admin,
    orm_get_all_admins,
    orm_get_all_users,
    orm_get_chatid_by_phone,
    orm_get_user,
    orm_get_users_by_group,
)

from bot.auth.user_verification import INITIAL_ADMIN_KB
from bot.handlers.user_handlers import Form
from bot.keyboards.inline import get_callback_btns, inline_actions_on_users
from bot.send_messages.newsletter import send_message_to_user, send_photo_to_user, send_video_to_user


class AddAdmin(StatesGroup):
    phone_input = State() 
    confirm = State()     
    none = State()

class AddUser(StatesGroup):
    phone_input = State()
    select_group = State()

class SearchUser(StatesGroup):
    waiting_for_phone = State()

class SendMessage(StatesGroup):
    waiting_for_message = State()

admin_router = Router()
admin_router.message.filter(IsAdmin())

ADMIN_KB = get_keyboard(
    "Добавить администратора",
    "Добавить пользователя",
    "Список пользователей",
    "Найти пользователя",
    "Отправить сообщение",
    "Список администраторов",
    "Назад",
    placeholder="Выберите действие",
    sizes=(2, 2, 2, 1),
)


@admin_router.message(F.text.casefold() == "админ панель")
async def check_command(message: types.Message, state: FSMContext) -> None:
    """Обрабатывает команду для открытия админ панели.

    Args:
        message (types.Message): Сообщение, полученное от админиистратора.
        state (FSMContext): Состояние машины состояний.
    """
    await state.set_state(AddAdmin.none)
    await message.answer("✨ Выберите действие, которое хотите выполнить:", reply_markup=ADMIN_KB)


@admin_router.message(F.text.casefold() == 'назад')
async def back(message: types.Message, state: FSMContext)-> None:
    """Обрабатывает команду для возврата на предыдущий шаг.

    Args:
        message (types.Message): Сообщение, полученное от админиистратора.
        state (FSMContext): Состояние машины состояний.
    """
    await state.set_state(Form.search)
    await message.answer('🔙 Вы вернулись на предыдущий шаг. Как я могу помочь вам дальше?', reply_markup=INITIAL_ADMIN_KB)


@admin_router.message(F.text.casefold() == 'добавить пользователя')
async def create_user(message: types.Message, state: FSMContext)-> None:
    """Обрабатывает команду для начала процесса добавления пользователя.

    Args:
        message (types.Message): Сообщение, полученное от админиистратора.
        state (FSMContext): Состояние машины состояний.
    """
    await state.set_state(AddUser.phone_input)  
    await message.answer("📞 <b>Пожалуйста, введите номер телефона (без плюса):</b>\n"
                         "Не забудьте проверить, что номер правильный!")
    bot_logger.log('info', f'Администратор {message.from_user.username} инициировал добавление нового Пользователя.')


@admin_router.message(F.text.casefold() == 'добавить администратора')
async def create_administrator(message: types.Message, state: FSMContext)-> None:
    """Обрабатывает команду для начала процесса добавления администратора.

    Args:
        message (types.Message): Сообщение, полученное от админиистратора.
        state (FSMContext): Состояние машины состояний.
    """
    await state.set_state(AddAdmin.phone_input)
    await message.answer("📞 <b>Пожалуйста, введите номер телефона администратора (без плюса):</b>\n"
                         "Не забудьте проверить, что номер правильный!")
    bot_logger.log('info', f'Администратор {message.from_user.username} инициировал добавление нового администратора.')


@admin_router.message(F.text.casefold() == "список пользователей")
async def get_all_users(message: types.Message, session: AsyncSession) -> None:
    """Обрабатывает команду для получения списка всех пользователей и их групп.

    Args:
        message (types.Message): Сообщение, полученное от админиистратора.
        session (AsyncSession): Асинхронная сессия базы данных.
    """
    try:
        users = await orm_get_all_users(session)  

        if not users:
            await message.answer("🚫 Список пользователей пуст.")
            return

        user_list = "📋 Список пользователей:\n\n"

        for index, user in enumerate(users, start=1):
            group_name = user.group.name if user.group else "Нет группы"
            user_list += f"{index}. 📞 Номер: <b>+{user.phone}</b>, Группа: <b>{group_name}</b>\n"

            keyboard_actions_on_user = inline_actions_on_users(user)

            await message.answer(
                f"{index}. 📞 Номер: <b>+{user.phone}</b>, Группа: <b>{group_name}</b>",
                reply_markup=keyboard_actions_on_user
            )

    except Exception as e:
        bot_logger.log('error', f"Ошибка получения списка пользователей: {e}")
        await message.answer("❌ Произошла ошибка при получении списка пользователей. Пожалуйста, попробуйте позже.")

@admin_router.message(F.text.casefold() == "список администраторов")
async def get_all_admins(message: types.Message, session: AsyncSession) -> None:
    """Обрабатывает команду для получения списка всех пользователей и их групп.

    Args:
        message (types.Message): Сообщение, полученное от админиистратора.
        session (AsyncSession): Асинхронная сессия базы данных.
    """
    try:
        admins = await orm_get_all_admins(session)  



        user_list = "📋 Список администраторов:\n\n"

        for index, admin in enumerate(admins, start=1):
            user_list += f"{index}. 📞 Номер: <b>+{admin.phone}</b>,\n"

            list_of_admins = get_callback_btns(
                btns={
                    'Удалить администратора': f'delete_admin_{admin.phone}',
                },
                sizes=(2, 1)
            )

            await message.answer(
                f"{index}. 📞 Номер: <b>+{admin.phone}</b>",
                reply_markup=list_of_admins
            )

    except Exception as e:
        bot_logger.log('error', f"Ошибка получения списка администраторов: {e}")
        await message.answer("❌ Произошла ошибка при получении списка администраторов. Пожалуйста, попробуйте позже.")



@admin_router.message(F.text.casefold() == 'найти пользователя')
async def find_user(message: types.Message, state: FSMContext)-> None:
    """Обрабатывает команду для начала процесса добавления администратора.

    Args:
        message (types.Message): Сообщение, полученное от админиистратора.
        state (FSMContext): Состояние машины состояний.
    """
    await message.answer(
        "Вы можете вводить номер как с пробелами, так и без них. "
        "Пример: <b>375 33 350 78 90</b> или <b>375333507890</b>. 🥺📞"
        )
    await state.set_state(SearchUser.waiting_for_phone)


@admin_router.message(F.text.casefold() == "отправить сообщение")
async def start_send_message_to_group(message: types.Message, session: AsyncSession) -> None:
    """Начинает процесс отправки сообщения всем пользователям группы.
    
    Args:
        message (types.Message): Сообщение, полученное от админиистратора.
        session (AsyncSession): Асинхронная сессия базы данных.
    
    """
    groups = await get_groups(session)
    btns = {group.name: f'group_message_{group.id}' for group in groups}
    await message.answer("✅ Пожалуйста, выберите группу:", reply_markup=get_callback_btns(btns=btns))


@admin_router.callback_query(F.data.startswith("group_message_"))
async def select_group_for_message(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Обрабатывает выбор группы для отправки сообщения.
    
    Args:
        callback (types.CallbackQuery): CallbackQuery от администратора.
        state (FSMContext): Контекст состояния для хранения данных пользователя.
    
    """
    group_id = int(callback.data.split('_')[2])
    await state.update_data({'selected_group_id': group_id})
    
    await callback.answer("✏️ Пожалуйста, введите сообщение (это может быть текст, фото или видео), которое вы хотите отправить всем пользователям этой группы:")
    await callback.message.edit_text("✏️ Пожалуйста, введите сообщение (это может быть текст, фото или видео), которое вы хотите отправить всем пользователям этой группы:")
    await state.set_state(SendMessage.waiting_for_message)


@admin_router.message(SendMessage.waiting_for_message)
async def process_group_message(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    """Обрабатывает сообщение от администратора и отправляет его всем пользователям группы.
    
    Args:
        message (types.Message): Сообщение, отправленное администратором.
        state (FSMContext): Контекст состояния для хранения данных пользователя.
        session (AsyncSession): Асинхронная сессия базы данных.
    
    """
    user_data = await state.get_data()
    group_id = user_data.get('selected_group_id')

    users = await orm_get_users_by_group(session, group_id)

    if not users:
        await message.answer("🚫 В данной группе нет пользователей.")
        return

    if message.photo:
        photo = message.photo[-1].file_id 
        for user in users:
            phone_number = f"{user.phone}" if not user.phone.startswith('+') else user.phone
            chat_id = await orm_get_chatid_by_phone(session, phone_number)
            if chat_id:
                await send_photo_to_user(message.bot, chat_id, photo, message.caption)

    elif message.video:
        video = message.video.file_id 
        for user in users:
            phone_number = f"{user.phone}" if not user.phone.startswith('+') else user.phone
            chat_id = await orm_get_chatid_by_phone(session, phone_number)
            if chat_id:
                await send_video_to_user(message.bot, chat_id, video, message.caption)

    else:
        for user in users:
            phone_number = f"{user.phone}" if not user.phone.startswith('+') else user.phone
            chat_id = await orm_get_chatid_by_phone(session, phone_number)
            if chat_id:
                await send_message_to_user(message.bot, chat_id, message.text)

    await message.answer("✅ Сообщение успешно отправлено всем пользователям группы.")


@admin_router.message(SearchUser.waiting_for_phone)
async def process_phone_number(message: types.Message, session: AsyncSession) -> None:
    """Обрабатывает введённый номер телефона и ищет пользователя в базе данных.
    
    Args:
        message (types.Message): Сообщение, содержащее номер телефона.
        session (AsyncSession): Асинхронная сессия базы данных.
    
    """
    try:
        phone_number = message.text.strip().replace(" ", "") 

        if not phone_number.isdigit() or len(phone_number) < 10:
            await message.answer(
                "❌ Ой! Неверный номер телефона."
                "Пожалуйста, убедитесь, что вводите корректный номер. "
                "Вы можете вводить номер как с пробелами, так и без них. "
                "Пример: <b>375 33 350 78 90</b> или <b>375333507890</b>. 🥺📞"
            )
            return

        user = await orm_get_user(session, phone_number)
        
        if user:
            group_name = await get_group_by_id(session, user.group_id)
            keyboard_actions_on_user = inline_actions_on_users(user)
            await message.answer(
                f"Пользователь найден: <b>+{user.phone}</b>, Группа: <b>{group_name}</b>",
                reply_markup=keyboard_actions_on_user
            )
        else:
            await message.answer("Пользователь с таким номером телефона не найден.")

    except ValueError as ve:
        bot_logger.log('error', f"Ошибка при обработке номера телефона: {ve}")
        await message.answer(
            "❌ Произошла ошибка при обработке номера телефона. "
            "Пожалуйста, убедитесь, что вводите корректный номер. "
            "Вы можете вводить номер как с пробелами, так и без них. "
            "Пример: <b>375 33 350 78 90</b> или <b>375333507890</b>. 🥺📞"
        )    
    except Exception as e:
        bot_logger.log('error', f"Необработанная ошибка: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте снова позже.")


@admin_router.callback_query(F.data.startswith('delete_user_'))
async def delete_user(callback_query: types.CallbackQuery, session: AsyncSession) -> None:
    """Удаляет пользователя по номеру телефона, переданному через callback_data.
    
    Args:
        callback_query (types.CallbackQuery): CallbackQuery от пользователя.
        session (AsyncSession): Асинхронная сессия базы данных.
    
    """
    phone = callback_query.data.split('_')[-1]

    user = await orm_get_user(session, phone)

    if not user:
        await callback_query.answer("Пользователь с таким номером не найден.")
        return

    try:
        await orm_delete_user(session, user)
        await callback_query.answer(f"Пользователь с номером +{user.phone} был удален.")
        await callback_query.message.edit_text(f"Пользователь c номером +{user.phone} был удален", reply_markup=None)

    except Exception as e:
        await callback_query.answer(f"❌ Произошла ошибка при удалении пользователя: {e}")
        bot_logger.log('error', f"Ошибка при удалении пользователя с номером +{user.phone}: {e}")

@admin_router.callback_query(F.data.startswith('delete_admin_'))
async def delete_admin(callback_query: types.CallbackQuery, session: AsyncSession) -> None:
    """Удаляет пользователя по номеру телефона, переданному через callback_data.
    
    Args:
        callback_query (types.CallbackQuery): CallbackQuery от пользователя.
        session (AsyncSession): Асинхронная сессия базы данных.
    
    """
    phone = callback_query.data.split('_')[-1]

    admin = await orm_get_admin(session, phone)

    try:
        await orm_delete_admin(session, admin)
        await callback_query.answer(f"Администратор с номером +{admin.phone} был удален.")
        await callback_query.message.edit_text(f"Администратор c номером +{admin.phone} был удален", reply_markup=None)

    except Exception as e:
        await callback_query.answer(f"❌ Произошла ошибка при удалении администратора: {e}")
        bot_logger.log('error', f"Ошибка при удалении администратора с номером +{admin.phone}: {e}")


@admin_router.callback_query(F.data.startswith("select_group_"))
async def confirm_user_addition(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext)-> None:
    """Подтверждает добавление пользователя в выбранную группу.

    Args:
        callback (types.CallbackQuery): Объект обратного вызова от администратора.
        session (AsyncSession): Асинхронная сессия базы данных.
        state (FSMContext): Состояние машины состояний.
    """
    try:
        group_id = int(callback.data.split('_')[2])
        user_data = await state.get_data()
        phone_number = user_data.get('add_user_phone')
        hashed_password = user_data.get('add_user_password')


        name_group = await get_group_by_id(session, group_id)

        await orm_add_user(session, phone_number, hashed_password, group_id)

        await callback.answer("✅ Новый пользователь успешно добавлен")
        await callback.message.edit_text(
            f"🎉 Поздравляю! Новый пользователь с номером <b>+{phone_number}</b> успешно добавлен в группу <b>{name_group}</b>!\n",
            reply_markup=None
        )

    except Exception as e:
        bot_logger.log('error',f"Ошибка при добавлении пользователя: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при добавлении пользователя. Пожалуйста, попробуйте позже.")


@admin_router.callback_query(F.data.startswith('change_group_'))
async def change_group_user(callback_query: types.CallbackQuery, session: AsyncSession) -> None:
    """Меняет группу пользователя по номеру телефона, переданному через callback_data.
    
    Args:
        callback_query (types.CallbackQuery): CallbackQuery от администратора с данными о новой группе и телефоне.
        session (AsyncSession): Асинхронная сессия базы данных.
    
    """
    data = callback_query.data.split('_')[-1] 
    id_group, phone = data.split(', ') 
    group_name = await get_group_by_id(session, int(id_group))

    group_mapping = {
        '1': ('2', 'FWS'),
        '2': ('1', 'FWD')
    }

    if id_group in group_mapping:
        new_id_group, group_name = group_mapping[id_group]

    user = await orm_get_user(session, phone)
    
    user.group_id = int(new_id_group)
    await session.commit()
    await callback_query.answer(f"Группа пользователя обновлена на {group_name}.")
    
    keyboard_actions_on_user = inline_actions_on_users(user)
    await callback_query.message.edit_text(f" 📞 Номер: +{user.phone}, Группа: {group_name}", reply_markup=keyboard_actions_on_user)


@admin_router.message(AddAdmin.phone_input)
async def input_phone(message: types.Message, state: FSMContext)-> None:
    """Обрабатывает ввод номера телефона администратора.

    Args:
        message (types.Message): Объект message.
        state (FSMContext): Состояние машины состояний.
    """
    try:
        phone_number = message.text.strip().replace(" ", "") 

        if not phone_number.isdigit() or len(phone_number) < 10:
            await message.answer(
            "❌ Ой! Неверный номер телефона."
            "Пожалуйста, убедитесь, что вводите корректный номер. "
            "Вы можете вводить номер как с пробелами, так и без них. "
            "Пример: <b>375 33 350 78 90</b> или <b>375333507890</b>. 🥺📞"
            )
            return

        password, hashed_password = generate_hashed_password()
        await state.update_data({'add_admin_phone': phone_number, 'add_admin_password': hashed_password})

        await state.set_state(AddAdmin.confirm)

        await message.answer(
            f"🔔 Вы собираетесь добавить нового администратора с номером: <b>+{phone_number}</b>\n"
            f"🔑 Вот его пароль для доступа: <b>{password}</b>\n\n"
            "✅ <b>Пожалуйста, подтвердите добавление:</b>\n"
            "Ваш новый администратор будет иметь возможность управлять важными функциями бота. Это действительно важно!",
            reply_markup=get_callback_btns(btns={'Да': 'add_', 'Нет': 'cancel_'}, sizes=(2, 1))
        )
    except Exception as e:
        bot_logger.log('error',f"Ошибка при вводе номера телефона администратора: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте снова.")


@admin_router.message(AddUser.phone_input)
async def process_phone_input(message: types.Message, state: FSMContext, session: AsyncSession)-> None:
    """Обрабатывает ввод номера телефона пользователя.

    Args:
        message (types.Message): Объект message.
        state (FSMContext): Состояние машины состояний.
        session (AsyncSession): Асинхронная сессия базы данных.
    """
    try:
        phone_number = message.text.strip().replace(" ", "") 

        if not phone_number.isdigit() or len(phone_number) < 10:
            await message.answer(
            "❌ Ой! Неверный номер телефона."
            "Пожалуйста, убедитесь, что вводите корректный номер. "
            "Вы можете вводить номер как с пробелами, так и без них. "
            "Пример: <b>375 33 350 78 90</b> или <b>375333507890</b>. 🥺📞"
            )
            return

        password, hashed_password = generate_hashed_password()

        groups = await get_groups(session)
        btns = {group.name: f'select_group_{group.id}' for group in groups}

        await state.update_data({'add_user_phone': phone_number, 'add_user_password': hashed_password})

        await message.answer(
            f"🔔 Вы собираетесь добавить нового пользователя с номером: <b>+{phone_number}</b>\n"
            f"🔑 Вот его пароль для доступа: <b>{password}</b>\n\n"
            "⚠️ <b>Пожалуйста, скопируйте пароль, так как после выбора группы он станет недоступен.</b>\n\n"
            "✅ <b>Пожалуйста, выберите группу папок, которые он сможет получать:</b>\n",
            reply_markup=get_callback_btns(btns=btns)
        )
    except Exception as e:
        bot_logger.log('error', f"Ошибка при вводе номера телефона пользователя: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте снова.")


@admin_router.callback_query(F.data.startswith("add_"))
async def confirm_addition(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext)-> None:
    """Подтверждает добавление администратора.

    Args:
        callback (types.CallbackQuery): Объект обратного вызова от пользователя.
        session (AsyncSession): Асинхронная сессия базы данных.
        state (FSMContext): Состояние машины состояний.
    """
    try:
        user_data = await state.get_data()
        phone_number = user_data.get('add_admin_phone')
        hashed_password = user_data.get('add_admin_password')

        await orm_add_administrator(session, phone_number, hashed_password)

        await callback.answer("✅ Новый администратор успешно добавлен")
        await callback.message.edit_text(
            f"🎉 Поздравляю! Новый администратор с номером <b>+{phone_number}</b> успешно добавлен!\n"
            "Если вам нужно добавить еще кого-то или у вас есть другие вопросы, просто дайте знать! 😊",
            reply_markup=None,
        )
    except Exception as e:
        bot_logger.log('error', f"Ошибка при добавлении администратора: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при добавлении администратора. Пожалуйста, попробуйте позже.")


@admin_router.callback_query(F.data.startswith("cancel_"))
async def cancel_addition(callback: types.CallbackQuery)-> None:
    """Отменяет добавление администратора.

    Args:
        callback (types.CallbackQuery): Объект обратного вызова от пользователя.
    """
    await callback.answer("❌ Добавление отменено")
    await callback.message.edit_text(
        "🚫 Добавление администратора было отменено. Если вам нужно что-то еще, просто дайте знать!\n"
        "Я здесь, чтобы помочь вам! 😊",
        reply_markup=None,
    )

