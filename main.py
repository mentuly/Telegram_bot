import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from dotenv import load_dotenv

from scheduler import setup_scheduler
from handlers.daily import send_daily_message

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

AUTHORIZED_USERS = []

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        AUTHORIZED_USERS.append(user_id)
        await message.answer("✅ Ви підписані на щоденні повідомлення!")
        await send_daily_message(bot, user_id)
    else:
        await message.answer("🔔 Ви вже підписані.")

async def main():
    for user_id in AUTHORIZED_USERS:
        await send_daily_message(bot, user_id)

    setup_scheduler(bot, AUTHORIZED_USERS[0] if AUTHORIZED_USERS else 0)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())