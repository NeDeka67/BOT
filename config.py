from aiogram import Bot, Dispatcher
import os

bot = Bot(token=os.getenv("BOT_TOKEN"))  # Достаёт токен из .env
dp = Dispatcher(bot)