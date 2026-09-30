import os
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ChatMemberStatus
from aiogram.types import FSInputFile

# --- НАСТРОЙКИ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ RENDER ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Числовой ID вашего канала @FenixAhk

# Точные ссылки по ТЗ
CHANNEL_URL = "https://t.me"
VPN_BOT_URL = "https://t.me"
STARS_BOT_URL = "https://t.me"

ZIP_FILE_NAME = "ahk.zip"
BANNER_IMAGE_PATH = "banner.jpg"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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

# Клавиатура подписки (Крутые иконки)
def get_subscription_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔥 ПОДПИСАТЬСЯ НА FENIX AHK 🔥", url=CHANNEL_URL)
    builder.button(text="⚡️ Я ПОДПИСАЛСЯ, ПУСТИ! ⚡️", callback_data="check_subscription")
    builder.adjust(1)
    return builder.as_markup()

# Главное меню (Жирный стиль + Иконки)
def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 ПОДКЛЮЧИТЬ PHOENIX VPN 🌐", url=VPN_BOT_URL)
    builder.button(text="⭐ ЗАПУСТИТЬ FENIX STARS ⭐", url=STARS_BOT_URL)
    builder.button(text="🎁 СКАЧАТЬ АХК ДЛЯ AMAZING RP 🎁", callback_data="get_ahk")
    builder.adjust(1)
    return builder.as_markup()

# Команда /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_subscribed = await is_subscribed(message.from_user.id)
    
    if user_subscribed:
        await send_main_menu(message.chat.id)
    else:
        await message.answer(
            "🛑 **ДОСТУП ОГРАНИЧЕН!** 🛑\n\n"
            "👋 Привет, боец! Чтобы забрать эксклюзивный **пак актуального AHK для Amazing RP**, "
            "а также открыть доступ к нашим приватным сервисам, тебе нужно выполнить одно простое условие:\n\n"
            "📌 **Подпишись на наш главный канал проекта!** Нажимай на кнопку ниже 👇",
            parse_mode="Markdown",
            reply_markup=get_subscription_keyboard()
        )

# Кнопка проверки
@dp.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: types.CallbackQuery):
    user_subscribed = await is_subscribed(callback.from_user.id)
    
    if user_subscribed:
        await callback.answer("👑 Успешно! Доступ разблокирован.", show_alert=False)
        await callback.message.delete()
        await send_main_menu(callback.message.chat.id)
    else:
        await callback.answer("❌ Ошибка! Ты не подписался на канал @FenixAhk. Давай быстрее, мы ждем!", show_alert=True)

# Красивое меню с текстом и кнопками
async def send_main_menu(chat_id: int):
    caption_text = (
        "🦅 **ПРОЕКТ FENIX ПРИВЕТСТВУЕТ ТЕБЯ!** 🦅\n\n"
        "Вы успешно верифицировали свой аккаунт. Специально от **Fenix_dinero** для всех игроков **Amazing RP** открыт доступ к лучшим инструментам:\n\n"
        "⚡️ **@fenixVPNrobot** — забудь про лаги, высокий пинг и блокировки. Стабильное соединение для комфортного капта и работы.\n\n"
        "💎 **@Fenix_Stars_bot** — наш элитный сервис для взаимодействия со звездами.\n\n"
        "🛸 **Скачивай софт:** Жми на кнопку **'СКАЧАТЬ АХК'** ниже, архив прилетит автоматически прямо в этот чат!"
    )
    
    if os.path.exists(BANNER_IMAGE_PATH):
        await bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(BANNER_IMAGE_PATH),
            caption=caption_text,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=caption_text,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# Выдача файла AHK
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
                "📦 **ВАШ АХК-ПАК ГОТОВ К РАБОТЕ!** 📦\n\n"
                "Разработчик: **Fenix_dinero**\n"
                "Специально для: **Amazing RP**\n\n"
                "📂 Распакуйте скачанный `.zip` архив и запускайте скрипты перед заходом в игру. Удачи на сервере! 🔥"
            ),
            parse_mode="Markdown"
        )
    else:
        await callback.answer("⚠️ Файл ahk.zip потерялся по дороге. Админ уже чинит!", show_alert=True)

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
