import os
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ChatMemberStatus
from aiogram.types import FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# --- НАСТРОЙКИ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ RENDER ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Числовой ID канала @FenixAhk
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # Твой числовой Telegram ID для доступа к админке

CHANNEL_URL = "tg://resolve?domain=FenixAhk"
VPN_BOT_URL = "tg://resolve?domain=fenixVPNrobot&start=click"
STARS_BOT_URL = "tg://resolve?domain=fenix_Stars_bot&start=click"

ZIP_FILE_NAME = "ahk.zip"
BANNER_IMAGE_PATH = "banner.jpg"

# Внутренняя БД в оперативной памяти для хранения базы юзеров
users_db = set()

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- СОСТОЯНИЯ ДЛЯ РАССЫЛКИ ---
class AdminStates(StatesGroup):
    waiting_for_broadcast_content = State()

# --- ВЕБ-СЕРВЕР ДЛЯ СЛУЖБЫ RENDER ---
async def handle_ping(request):
    return web.Response(text="Бот Fenix активен!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Мониторинг запущен на порту {port}")

# --- ПРОВЕРКА ПОДПИСКИ ---
async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
    except Exception as e:
        logging.error(f"Ошибка проверки подписки в @FenixAhk: {e}")
        return False

def get_subscription_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 ПОДПИСАТЬСЯ НА @FenixAhk 📢", url=CHANNEL_URL)
    builder.button(text="✅ Я ПОДПИСАЛСЯ, ПУСТИ! ✅", callback_data="check_subscription")
    builder.adjust(1)
    return builder.as_markup()

def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 ПОДКЛЮЧИТЬ @fenixVPNrobot 🌐", url=VPN_BOT_URL)
    builder.button(text="⭐ ЗАПУСТИТЬ @Fenix_Stars_bot ⭐", url=STARS_BOT_URL)
    builder.button(text="🎁 СКАЧАТЬ АХК ДЛЯ AMAZING RP 🎁", callback_data="get_ahk")
    builder.adjust(1)
    return builder.as_markup()

# --- ПАНЕЛЬ АДМИНИСТРАТОРА ---
def get_admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 СТАТИСТИКА БАЗЫ", callback_data="admin_stats")
    builder.button(text="📢 ЗАПУСТИТЬ РАССЫЛКУ", callback_data="admin_broadcast")
    builder.adjust(1)
    return builder.as_markup()

# Команда /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    users_db.add(message.from_user.id)  # Логируем юзера в базу данных рассылки
    user_subscribed = await is_subscribed(message.from_user.id)
    
    if user_subscribed:
        await send_main_menu(message.chat.id)
    else:
        await message.answer(
            "🛑 <b>ДОСТУП ОГРАНИЧЕН!</b> 🛑\n\n"
            "👋 Привет, боец! Чтобы забрать эксклюзивный <b>пак актуального AHK для Amazing RP</b>, "
            "а также открыть доступ к нашим приватным сервисам, тебе нужно выполнить одно простое условие:\n\n"
            "📌 <b>Подпишись на наш главный канал проекта!</b> Нажимай на кнопку ниже 👇",
            parse_mode="HTML",
            reply_markup=get_subscription_keyboard()
        )

# Проверка подписки по кнопке
@dp.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: types.CallbackQuery):
    user_subscribed = await is_subscribed(callback.from_user.id)
    
    if user_subscribed:
        await callback.answer("👑 Успешно! Доступ разблокирован.", show_alert=False)
        await callback.message.delete()
        await send_main_menu(callback.message.chat.id)
    else:
        await callback.answer("❌ Ошибка! Ты не подписался на канал @FenixAhk. Давай быстрее, мы ждем!", show_alert=True)

# Главное меню проекта
async def send_main_menu(chat_id: int):
    caption_text = (
        "🦅 <b>ПРОЕКТ FENIX ПРИВЕТСТВУЕТ ТЕБЯ!</b> 🦅\n\n"
        "Вы успешно верифицировали свой аккаунт. Специально от <b>Fenix_dinero</b> для всех игроков <b>Amazing RP</b> открыт доступ к лучшим инструментам:\n\n"
        "⚡️ <b>@fenixVPNrobot</b> — забудь про лаги, высокий пинг и блокировки. Стабильное соединение для комфортного капта и работы.\n\n"
        "💎 <b>@Fenix_Stars_bot</b> — наш элитный сервис для взаимодействия со звездами.\n\n"
        "🛸 <b>Скачивай AHK:</b> Жми на кнопку <b>'СКАЧАТЬ АХК'</b> ниже, архив прилетит автоматически прямо в этот чат!"
    )
    
    if os.path.exists(BANNER_IMAGE_PATH):
        await bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(BANNER_IMAGE_PATH),
            caption=caption_text,
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=caption_text,
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )

# Скачивание файла AHK
@dp.callback_query(F.data == "get_ahk")
async def send_ahk_file(callback: types.CallbackQuery):
    if not await is_subscribed(callback.from_user.id):
        await callback.answer("🔒 Доступ заблокирован! Сначала подпишись на @FenixAhk", show_alert=True)
        return

    if os.path.exists(ZIP_FILE_NAME):
        await callback.answer("🚀 Передаем файлы на базу...")
        await bot.send_document(
            chat_id=callback.message.chat.id,
            document=FSInputFile(ZIP_FILE_NAME),
            caption=(
                "📦 <b>ВАШ АХК-ПАК ГОТОВ К РАБОТЕ!</b> 📦\n\n"
                "Разработчик: <b>Fenix_dinero</b>\n"
                "Специально для: <b>Amazing RP</b>\n\n"
                "📂 Распакуйте скачанный <code>.zip</code> архив и запускайте AHK перед заходом в игру. Удачи на сервере! 🔥"
            ),
            parse_mode="HTML"
        )
    else:
        await callback.answer("⚠️ Файл ahk.zip потерялся по дороге. Админ уже чинит!", show_alert=True)

# --- УПРАВЛЕНИЕ АДМИНКОЙ ДЛЯ FENIX ДИНЕРО ---
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        Return
    
    await message.answer(
        "⚡️ <b>ДОБРО ПОЖАЛОВАТЬ В ЗАКРЫТУЮ АДМИН-ПАНЕЛЬ FENIX</b> ⚡️\n\n"
        "Выбери необходимое действие на интерактивной панели ниже:",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )

@dp.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        Return
    total_users = len(users_db)
    await callback.answer(f"📊 Всего уникальных пользователей в базе: {total_users}", show_alert=True)

@dp.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        Return
    await callback.message.answer("📢 <b>Отправь мне контент для рассылки.</b>\nЭто может быть как обычный текст, так и пост с картинкой/баннером:", parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_broadcast_content)
    await callback.answer()

@dp.message(AdminStates.waiting_for_broadcast_content)
async def process_broadcast_content(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        Return
    
    await state.clear()
    await message.answer("🚀 <b>Рассылка запущена по всей базе пользователей...</b>", parse_mode="HTML")
    
    success_count = 0
    fail_count = 0
    
    for user_id in list(users_db):
        try:
            if message.photo:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=message.photo[-1].file_id,
                    caption=message.caption,
                    caption_entities=message.caption_entities
                )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=message.text,
                    entities=message.entities
                )
            success_count += 1
            await asyncio.sleep(0.05)  # Защита от флуд-лимитов Telegram
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
            fail_count += 1
            
    await message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 Успешно доставлено: <code>{success_count}</code>\n"
        f"❌ Ошибки (бот заблокирован): <code>{fail_count}</code>",
        parse_mode="HTML"
    )

# --- ЗАПУСК ПРОЕКТА ---
async main():
    await bot.delete_webhook(drop_pending_updates=True)
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
