import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(
    token=os.getenv('BOT_TOKEN'),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Проверка администратора
def is_admin(user_id: int) -> bool:
    return str(user_id) == os.getenv('ADMIN_ID')

# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("🎨 Привет! Присылай мне идеи для артов или постов.")

@dp.message(Command("help"))
async def help(message: types.Message):
    await message.answer("Просто отправь мне свою идею, и я передам её автору!")

@dp.message(F.text & ~F.text.startswith('/'))
async def forward_to_admin(message: types.Message):
    if is_admin(message.from_user.id):
        return
    
    admin_id = os.getenv('ADMIN_ID')
    user = message.from_user
    
    try:
        await bot.send_message(
            admin_id,
            f"📨 Новое предложение от @{user.username} (ID: {user.id}):\n"
            f"━━━━━━━━━━━━━━\n"
            f"{message.text}\n"
            f"━━━━━━━━━━━━━━\n"
            f"Ответить: /reply_{user.id}"
        )
        await message.answer("✅ Идея отправлена!")
    except Exception as e:
        logger.error(f"Ошибка пересылки: {e}")
        await message.answer("❌ Не удалось отправить идею")

@dp.message(F.photo | F.video | F.document)
async def forward_media(message: types.Message):
    if is_admin(message.from_user.id):
        return
    
    admin_id = os.getenv('ADMIN_ID')
    user = message.from_user
    
    try:
        caption = (
            f"📎 Медиа от @{user.username} (ID: {user.id})\n"
            f"━━━━━━━━━━━━━━\n"
            f"{message.caption or ''}\n"
            f"━━━━━━━━━━━━━━\n"
            f"Ответить: /reply_{user.id}"
        )
        
        if message.photo:
            await bot.send_photo(admin_id, message.photo[-1].file_id, caption=caption)
        elif message.video:
            await bot.send_video(admin_id, message.video.file_id, caption=caption)
        elif message.document:
            await bot.send_document(admin_id, message.document.file_id, caption=caption)
            
        await message.answer("✅ Файл получен!")
    except Exception as e:
        logger.error(f"Ошибка пересылки медиа: {e}")
        await message.answer("❌ Не удалось отправить файл")

# ========== ОБРАБОТКА ОТВЕТОВ АДМИНА ==========

@dp.message(F.text.regexp(r'^/(reply|r)_(\d+)(?:\s+(.+))?$'))
async def reply_to_user(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Эта команда только для администратора!")
        return
    
    try:
        # Извлекаем user_id и текст ответа с помощью регулярного выражения
        import re
        match = re.match(r'^/(reply|r)_(\d+)(?:\s+(.+))?$', message.text)
        if not match:
            await message.answer("❌ Формат команды: /reply_123456 текст или /r_123456 текст")
            return
        
        _, user_id, reply_text = match.groups()
        reply_text = reply_text or "Спасибо за ваше предложение!"
        
        try:
            await bot.send_message(
                int(user_id),
                f"💌 Ответ от автора:\n━━━━━━━━━━━━━━\n{reply_text}\n━━━━━━━━━━━━━━"
            )
            await message.answer(f"✉️ Ответ отправлен пользователю {user_id}")
        except TelegramBadRequest as e:
            logger.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
            await message.answer("❌ Не удалось отправить (пользователь заблокировал бота?)")
        except ValueError as e:
            logger.error(f"Неверный ID пользователя: {user_id}, ошибка: {e}")
            await message.answer("❌ Неверный ID пользователя")
    except Exception as e:
        logger.error(f"Ошибка при обработке команды reply: {e}")
        await message.answer(f"❌ Ошибка: {e}")

# ========== ЗАПУСК БОТА ==========

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


