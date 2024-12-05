from aiogram import F, types, Router
from aiogram.filters import CommandStart

from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy.ext.asyncio import AsyncSession

from bot.auth.auth_function import get_auth_data
from bot.auth.user_verification import check_admin_credentials, check_user_credentials, get_variable_admin
from bot.database.orm_query import get_group_by_id, orm_add_chatid_for_user, orm_get_admin, orm_get_user
from bot.google.google_function import create_drive_service, get_drive_config, get_files_from_folder
from bot.keyboards.reply import get_keyboard
from bot.logging.logger import bot_logger

user_router = Router()
SERVICE_ACCOUNT_FILE, SCOPES = get_drive_config()
service = create_drive_service(SERVICE_ACCOUNT_FILE, SCOPES)


class Form(StatesGroup):
    auth = State()
    search = State()
    check = State()
    get = State()

@user_router.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext)-> None:
    try:
        start_message = (
            "👋 Приветствую вас, я <b>FileScout</b>! 🌟 Я — ваш надежный помощник для поиска и получения файлов из Google Диска. 📂\n\n"
            "С моей помощью вы можете быстро и легко найти нужные файлы, просто указав название папки! 📁\n\n"
            "Но для начала мне нужно убедиться, что это действительно вы, поэтому необходимо пройти аутентификацию. 🔑\n\n"
            "Как это работает:\n"
            "1️⃣ Нажмите на кнопку <b>Войти</b>, чтобы я мог убедиться, что это вы.\n"
            "2️⃣ Отправьте мне свой номер телефона, который поможет мне найти вас.\n"
            "3️⃣ Введите пароль, чтобы завершить вход в аккаунт.\n"
            "4️⃣ Как только вы войдете, сможете вводить название папки, и я помогу вам найти все файлы в ней! 📂\n\n"
            "Я обеспечу вашу безопасность, и только вы сможете получить доступ к файлам! 🔒\n\n"
            "Готовы? Тогда нажмите на кнопку <b>Войти</b>, чтобы начать! 👇"
        )
        get_phone_keyboard = get_keyboard(
            "",
            "🔑 Войти",
            placeholder="Нажми кнопку Войти, чтобы продолжить.",
            request_contact=1,
            sizes=(1,)
        )
        
        await state.set_state(Form.auth)
        await message.answer(start_message, reply_markup=get_phone_keyboard)
        bot_logger.log('info', 'Бот запущен, приветственное сообщение отправлено')

    except Exception as e:
        bot_logger.log('error', f'Ошибка в start_cmd: {e}')
        await message.answer("⚠️ Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже.")

@user_router.message((F.text == "🔑 Войти") | (F.contact), Form.auth)

async def handle_auth(message: types.Message, state: FSMContext)-> None:
    try:            
        if message.text == "🔑 Войти":
            phone, password = await get_auth_data(state)
            auth_message =(
            "🔒 Введите пароль для входа в ваш аккаунт:\n\n"
            "Пожалуйста, убедитесь, что вы вводите правильный пароль. 🛠️\n\n"
            "Как только вы введете пароль, вы получите доступ ко всем своим файлам и функциям. "
            "Давайте сделаем это вместе! 🚀"
            )            
            await message.answer(auth_message, reply_markup=ReplyKeyboardRemove())
            await state.update_data({'awaiting_password': True,'phone_number': phone, 'password': password })
            await state.set_state(Form.auth)

            bot_logger.log('info', f'Пользователь {message.from_user.username} нажал на кнопку "Войти"')

        elif message.contact:
            contact = message.contact
            phone_number = contact.phone_number
            login_message = (
            f"📱 Ваш логин: <b>+{phone_number}</b>. \n\n"
            "Теперь, чтобы завершить процесс входа, пожалуйста, введите свой пароль. 🔑\n\n"
            "Убедитесь, что вы вводите правильный пароль.\n\n "
            "Давайте продолжим, и вы сможете получить доступ ко всем своим файлам! 📂"
            )
            await message.answer(login_message, reply_markup=ReplyKeyboardRemove())
            await state.update_data({'awaiting_password': True,'phone_number': phone_number })
            await state.set_state(Form.auth)
            bot_logger.log('info', f'Пользователь {message.from_user.username} отправил контакт: {phone_number}')

    except Exception as e:
        bot_logger.log('error', f'Ошибка в handle_auth: {e}')
        await message.answer("⚠️ Произошла ошибка при авторизации. Пожалуйста, попробуйте снова.")

@user_router.message(F.text == "❌ Выйти") #Банальная очередность хэндлеров
async def exit_handler(message: types.Message, state: FSMContext)-> None:
    try:
        await state.set_state(Form.auth)
        logout_message = (
        "🚪 Вы успешно вышли из аккаунта. Мы надеемся, что ваше время было приятным!\n\n"
        "Чтобы вернуться и продолжить пользоваться всеми функциями нашего сервиса, "
        "просто нажмите кнопку <b>🔑 Войти.</b>\n\n"
        )
        await message.answer(logout_message, reply_markup=get_keyboard("🔑 Войти", placeholder="Что вас интересует?"))
        await state.update_data({'admin': False})
        bot_logger.log('info', f'Пользователь {message.from_user.username} вышел из аккаунта.')
    except Exception as e:
        bot_logger.log('error', f'Ошибка в exit_handler: {e}')
        await message.answer("⚠️ Произошла ошибка при выходе. Пожалуйста, попробуйте снова.")

@user_router.message(F.text, Form.auth)
async def auth(message: types.Message, state: FSMContext, session: AsyncSession)-> None:
    try:
        user_data = await state.get_data()
        phone_number, password = await get_auth_data(state)

        if not user_data.get('awaiting_password'):
            await message.answer("❗ Сначала нажмите кнопку <b>Войти</b>.")
            return

        password = message.text.strip()
        await state.update_data({"password": password})

        admin = await orm_get_admin(session, phone_number)
        if admin and await check_admin_credentials(admin, password, message):
            await state.set_state(Form.search) 
            await state.update_data({'admin': True, 'awaiting_password': False})

            return
        user = await orm_get_user(session, phone_number)

        if user and await check_user_credentials(user, password, message):
            await state.set_state(Form.search)
            await state.update_data({'awaiting_password': False}) 
            chat_id = message.chat.id
            await orm_add_chatid_for_user(session, chat_id, phone_number)
            return
        
        await message.answer("🚫 Пароль неверный или учетная запись не найдена. Попробуйте снова.")

    except Exception as e:
        bot_logger.log('error', f'Ошибка в auth: {e}')
        await message.answer("⚠️ Произошла ошибка при обработке. Пожалуйста, попробуйте снова.")

@user_router.message((F.text == "Поиск"))

async def search_catalog(message: types.Message, state: FSMContext)-> None:
    try:
        is_admin = await get_variable_admin(state)

        search_message = (
            "🔎 Пожалуйста, укажите номер каталога, который вы хотите найти. "
            "🗂️ Это поможет мне быстро и точно предоставить вам нужную информацию. "
            "✨"
        )     
        if is_admin:
            admin_keyboard = get_keyboard("❌ Выйти", "Админ панель", placeholder="Что вас интересует?")
            await message.answer(search_message, reply_markup=admin_keyboard)
        else:
            user_keyboard = get_keyboard("❌ Выйти", placeholder="Что вас интересует?")
            await message.answer(search_message, reply_markup=user_keyboard)

        await state.set_state(Form.get)
        bot_logger.log('info', f'Пользователь {message.from_user.username} начал поиск.')

    except Exception as e:
        bot_logger.log('error', f'Ошибка в search_catalog: {e}')
        await message.answer("⚠️ Произошла ошибка при поиске. Пожалуйста, попробуйте позже.")

@user_router.message(F.text != "Админ панель", Form.get)
async def get_files(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    folder_name = message.text.strip()
    
    try:
        user_data = await state.get_data()
        phone_number = user_data.get('phone_number')
        user = await orm_get_user(session, phone_number)
        
        group_name = await get_group_by_id(session, user.group_id)
        
        is_admin = await get_variable_admin(state)

        response_text, error = await get_files_from_folder(service, folder_name, None if is_admin else group_name)

        if error:
            bot_logger.log('error', f'Ошибка при получении файлов: {error}')
            await message.answer(f"❌ Ошибка: {response_text}")
        else:
            if is_admin:
                exit_keyboard = get_keyboard("❌ Выйти", "Админ панель", placeholder="Что вас интересует?")
            else:
                exit_keyboard = get_keyboard("❌ Выйти", placeholder="Что вас интересует?")
                
            await message.answer(response_text, reply_markup=exit_keyboard)

    except Exception as e:
        bot_logger.log('error', f'Необработанная ошибка в get_files: {e}')
        await message.answer("⚠️ Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.")