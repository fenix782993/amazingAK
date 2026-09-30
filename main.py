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

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

CHANNEL_URL = "tg://resolve?domain=FenixAhk"
VPN_BOT_URL = "tg://resolve?domain=fenixVPNrobot&start=click"
STARS_BOT_URL = "tg://resolve?domain=fenix_Stars_bot&start=click"

ZIP_FILE_NAME = "ahk.zip"
BANNER_IMAGE_PATH = "banner.jpg"

users_db = set()

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class AdminStates(StatesGroup):
    waiting_for_broadcast_content = State()
    waiting_for_ahk_file = State()

async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
    except Exception as e:
        logging.error(f"Subscription check error: {e}")
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

def get_admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 СТАТИСТИКА БАЗЫ", callback_data="admin_stats")
    builder.button(text="📢 ЗАПУСТИТЬ РАССЫЛКУ", callback_data="admin_broadcast")
    builder.button(text="🔄 ОБНОВИТЬ ФАЙЛ AHK.ZIP", callback_data="admin_update_file")
    builder.adjust(1)
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    users_db.add(message.from_user.id)
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

@dp.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: types.CallbackQuery):
    user_subscribed = await is_subscribed(callback.from_user.id)
    
    if user_subscribed:
        await callback.answer("👑 Успешно! Доступ разблокирован.", show_alert=False)
        await callback.message.delete()
        await send_main_menu(callback.message.chat.id)
    else:
        await callback.answer("❌ Ошибка! Ты не подписался на канал @FenixAhk. Давай быстрее, мы ждем!", show_alert=True)

async def send_main_menu(chat_id: int):
    caption_text = (
        "🦅 <b>ПРОЕКТ FENIX ПРИВЕТСТВУЕТ ТЕБЯ!</b> 🦅\n\n"
        "Вы успешно верифицировали свой аккаунт. Специально от <b>Fenix_dinero</b> для всех игроков <b>Amazing RP</b> открыт доступ к лучшим инструментам:\n\n"
        "⚡️ <b>@fenixVPNrobot</b> — забудь про лаги, высокий пинг и блокировки. Стабильное соединение для комфортного капта и работы.\n\n"
        "💎 <b>@Fenix_Stars_bot</b> — наш элитный сервис для взаимодействия со звездами.\n\n"
        "👑 <b>Скачивай AHK:</b> Жми на кнопку <b>'СКАЧАТЬ АХК'</b> ниже, архив прилетит автоматически прямо в этот чат!"
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

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    await message.answer(
        "⚡️ <b>ДОБРО ПОЖАЛОВАТЬ В ЗАКРЫТУЮ АДМИН-ПАНЕЛЬ FENIX</b> ⚡️\n\n"
        "Выбери необходимое действие на интерактивной панели ниже:",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )

@dp.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    total_users = len(users_db)
    await callback.answer(f"📊 Всего уникальных пользователей в базе: {total_users}", show_alert=True)

@dp.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.answer("📢 <b>Отправь мне контент для рассылки.</b>\nЭто может быть как обычный текст, так и пост с картинкой/баннером:", parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_broadcast_content)
    await callback.answer()

@dp.message(AdminStates.waiting_for_broadcast_content)
async def process_broadcast_content(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
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
            await asyncio.sleep(0.05)
        except Exception as e:
            logging.error(f"Broadcast failed for user {user_id}: {e}")
            fail_count += 1
            
    await message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 Успешно доставлено: <code>{success_count}</code>\n"
        f"❌ Ошибки (бот заблокирован): <code>{fail_count}</code>",
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "admin_update_file")
async def callback_admin_update_file(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.answer("📂 <b>Отправь мне новый файл архива в формате .zip</b>\nБот автоматически сохранит его как ahk.zip для скачивания пользователями:", parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_ahk_file)
    await callback.answer()

@dp.message(AdminStates.waiting_for_ahk_file)
async def process_ahk_file_update(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if not message.document or not message.document.file_name.endswith('.zip'):
        await message.answer("❌ <b>Ошибка!</b> Отправь файл строго в формате <code>.zip</code>!", parse_mode="HTML")
        return
        
    await state.clear()
    await message.answer("📥 <b>Загрузка и замена файла в системе...</b>", parse_mode="HTML")
    
    try:
        file_info = await bot.get_file(message.document.file_id)
        await bot.download_file(file_info.file_path, ZIP_FILE_NAME)
        await message.answer("✅ <b>Успешно!</b> Новый файл архива сохранен и готов к выдаче пользователям.", parse_mode="HTML")
    except Exception as e:
        logging.error(f"File download error: {e}")
        await message.answer(f"❌ <b>Критическая ошибка при сохранении файла:</b> {e}", parse_mode="HTML")

async def run_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

def main():
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Бот Fenix активен!"))
    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host='0.0.0.0', port=port)
if name == "main":
main()
