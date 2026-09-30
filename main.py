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
CHANNEL_ID = os.getenv("CHANNEL_ID")  # ID канала, например, -1002345678901

# Фиксированные данные по ТЗ
CHANNEL_URL = "https://t.me"
VPN_BOT_URL = "https://t.me"
STARS_BOT_URL = "https://t.me"

ZIP_FILE_NAME = "ahk.zip"
BANNER_IMAGE_PATH = "banner.jpg"

# Инициализация логирования и бота
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (ЧТОБЫ СЛУЖБА НЕ ПАДАЛА) ---
async def handle_ping(request):
    return web.Response(text="Бот активен и работает!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render передает порт в переменную среды PORT
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Веб-сервер мониторинга запущен на порту {port}")

# --- ЛОГИКА ТЕЛЕГРАМ-БОТА ---

# Функция проверки подписки
async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")
        # Если бота еще не добавили в админы канала, временно пропускаем, чтобы не крашился
        return False

# Клавиатура проверки подписки
def get_subscription_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Подписаться на Fenix AHK", url=CHANNEL_URL)
    builder.button(text="✅ Я подписался", callback_data="check_subscription")
    builder.adjust(1)
    return builder.as_markup()

# Главное меню (Переходы на ботов + Получить AHK)
def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🛡️ Войти в Phoenix VPN", url=VPN_BOT_URL)
    builder.button(text="⭐ Запустить Fenix Stars", url=STARS_BOT_URL)
    builder.button(text="📦 Получить AHK (ZIP)", callback_data="get_ahk")
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
            "👋 **Привет!** Чтобы получить эксклюзивный **AHK для Amazing RP**, "
            "а также доступ к нашим сервисам, подпишись на наш официальный канал!",
            parse_mode="Markdown",
            reply_markup=get_subscription_keyboard()
        )

# Обработка кнопки подтверждения подписки
@dp.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: types.CallbackQuery):
    user_subscribed = await is_subscribed(callback.from_user.id)
    
    if user_subscribed:
        await callback.answer("🎉 Подписка подтверждена!")
        await callback.message.delete()
        await send_main_menu(callback.message.chat.id)
    else:
        await callback.answer("❌ Вы всё ещё не подписались на канал @FenixAhk!", show_alert=True)

# Отправка красивого меню с баннером
async def send_main_menu(chat_id: int):
    caption_text = (
        "✨ **Добро пожаловать в главное меню Fenix!** ✨\n\n"
        "Вы успешно открыли доступ к приватным утилитам для **Amazing RP**.\n\n"
        "🚀 **Phoenix VPN** — идеальный пинг и стабильный обход любых блокировок в игре.\n"
        "⭐ **Fenix Stars** — наш официальный бот для взаимодействия со звёздами.\n\n"
        "⏬ Нажмите на кнопку **'Получить AHK'** ниже, чтобы скачать архив со скриптами."
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
        await callback.answer("🔒 Ошибка: Вы должны быть подписаны на @FenixAhk!", show_alert=True)
        return

    if os.path.exists(ZIP_FILE_NAME):
        await callback.answer("⏳ Отправка файла...")
        await bot.send_document(
            chat_id=callback.message.chat.id,
            document=FSInputFile(ZIP_FILE_NAME),
            caption="📂 **Ваш AHK-скрипт для Amazing RP успешно сгенерирован!**\nРаспакуйте архив и используйте во время игры.",
            parse_mode="Markdown"
        )
    else:
        await callback.answer("⚠️ Файл ahk.zip отсутствует на сервере. Обратитесь к админу.", show_alert=True)

# --- ЗАПУСК ВСЕХ КОМПОНЕНТОВ ---
async def main():
    # Запускаем веб-сервер для пинга от Render
    await start_web_server()
    # Запускаем поллинг бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
