import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = 'https://web-production-8dd7d.up.railway.app/'  # <- заміниш після деплою

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(commands=["start"])
async def start_handler(message: Message):
    await message.answer("Привіт!")

@dp.message()
async def echo_handler(message: Message):
    await message.answer(message.text)

async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()

async def index(request):
    return web.Response(text="Бот працює!", status=200)

app = web.Application()
app.router.add_get("/", index)

# Налаштовуємо webhook
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))