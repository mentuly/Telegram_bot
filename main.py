import os
import json
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
from dotenv import load_dotenv
import logging

from handlers.daily import register_handlers, send_daily_message
from scheduler import setup_scheduler
from data import users

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://web-production-8dd7d.up.railway.app/")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Зберігаємо авторизованих користувачів у пам'яті
AUTHORIZED_USERS = set(users.load_users())

# Команда /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        AUTHORIZED_USERS.add(user_id)
        users.save_user(user_id)  # якщо маєш таку функцію
        await message.answer("✅ Ви підписані на щоденні повідомлення!")
        await send_daily_message(bot, user_id)
        setup_scheduler(bot, user_id)
    else:
        await message.answer("🔔 Ви вже підписані.")

# Додаткові хендлери
register_handlers(dp)

# Webhook setup
async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)

    for user_id in AUTHORIZED_USERS:
        setup_scheduler(bot, user_id)

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()

async def index(request):
    return web.Response(text="Бот працює!", status=200)

# Запуск aiohttp-сервера
def run():
    app = web.Application()
    app.router.add_get("/", index)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    run()