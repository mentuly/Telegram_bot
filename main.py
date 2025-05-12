import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, IS_TEST_MODE, SEND_TIME, TIMEZONE, WEBHOOK_URL
from database import add_user, get_users, update_last_sent
from lessons import lessons
from datetime import datetime
import os
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

@dp.message(Command("start"))
async def start_handler(message: Message):
    add_user(message.from_user.id)
    await message.answer("Привіт! Починаємо твій 30-денний курс навчання 🧠")

async def send_lessons():
    users = get_users()
    now = datetime.now()
    print(f"Завдання відправлено в: {now}")

    if not users:
        print("Немає користувачів у базі даних!")

    for user_id, start_date_str, last_sent in users:
        print(f"Перевіряємо користувача {user_id}: останній відправлений день - {last_sent}")
        
        start_date = datetime.fromisoformat(start_date_str)
        days_passed = (now.date() - start_date.date()).days
        print(f"Кількість пройдених днів: {days_passed}")
        
        if days_passed >= len(lessons):
            print(f"Курс завершено для користувача {user_id}.")
            continue

        if days_passed > last_sent or (days_passed == 0 and last_sent == 0):

            text = lessons[days_passed]
            print(f"Відправка повідомлення: користувач {user_id}, день {days_passed}, завдання: {text}")
            await bot.send_message(user_id, f"📚 {text}")

            update_last_sent(user_id, days_passed)
            print(f"Оновлено останній день для користувача {user_id} на {days_passed}")
        elif days_passed == last_sent:
            print(f"Завдання вже відправлено користувачу {user_id}. Пропускаємо.")
            continue
        else:
            missed = days_passed - last_sent
            print(f"У користувача {user_id} пропуски. Відправляємо повідомлення.")
            await bot.send_message(user_id, f"📌 У тебе {missed} пропуск(ів). Хочеш надолужити?")

async def start_web_app():
    app = web.Application()
    app.router.add_get("/", index)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 5000)))
    await site.start()
    print("🌐 Web сервер запущено")

async def start_bot():
    if IS_TEST_MODE:
        print("Тестовий режим: завдання відправлятиметься кожні 30 секунд")
        scheduler.add_job(send_lessons, "interval", seconds=30)
    else:
        print(f"Завдання заплановано на час: {SEND_TIME.hour}:{SEND_TIME.minute}")
        scheduler.add_job(
            send_lessons,
            "cron",
            hour=SEND_TIME.hour,
            minute=SEND_TIME.minute,
            timezone=TIMEZONE
        )

    scheduler.start()
    await dp.start_polling(bot)

async def main():
    await asyncio.gather(
        start_web_app(),
        start_bot()
    )

# Webhook setup
async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()

async def index(request):
    return web.Response(text="Бот працює!", status=200)

if __name__ == "__main__":
    asyncio.run(main())