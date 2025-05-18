import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, IS_TEST_MODE, SEND_TIME, TIMEZONE
from database import add_user, get_users, update_last_sent
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import mark_incomplete, mark_complete, get_incomplete_tasks
from lessons import lessons
from datetime import datetime
import os
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

WEBHOOK_URL = 'https://web-production-8dd7d.up.railway.app/'
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

@dp.message(Command("start"))
async def start_handler(message: Message):
    add_user(message.from_user.id)
    await message.answer("Привіт! Починаємо твій 30-денний курс навчання 🧠")

@dp.message(Command("complete_task"))
async def complete_task_handler(message: Message):
    user_id = message.from_user.id
    incomplete_days = get_incomplete_tasks(user_id)

    if not incomplete_days:
        await message.answer("У тебе немає невиконаних завдань 🎉")
        return

    for day in incomplete_days:
        text = f"📌 День {day + 1}: {lessons[day]}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Завершено", callback_data=f"complete:{day}"),
             InlineKeyboardButton(text="❌ Все ще не завершено", callback_data=f"incomplete:{day}")]
        ])
        await message.answer(text, reply_markup=keyboard)

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
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Завершено", callback_data=f"complete:{days_passed}"),
                InlineKeyboardButton(text="❌ Не завершено", callback_data=f"incomplete:{days_passed}")]
            ])

            await bot.send_message(user_id, f"📚 {text}", reply_markup=keyboard)

            print(f"Відправка повідомлення: користувач {user_id}, день {days_passed}, завдання: {text}")
            await bot.send_message(user_id, f"📚 {text}")

            incomplete_days = get_incomplete_tasks(user_id)
            if incomplete_days:
                msg = "📌 У тебе залишились незавершені дні:\n"
                for day in incomplete_days:
                    msg += f"- День {day + 1}: {lessons[day]}\n"
                msg += "\nВикористай /complete_task щоб позначити виконані ✅"
                await bot.send_message(user_id, msg)

            update_last_sent(user_id, days_passed)
            print(f"Оновлено останній день для користувача {user_id} на {days_passed}")
        elif days_passed == last_sent:
            print(f"Завдання вже відправлено користувачу {user_id}. Пропускаємо.")
            continue
        else:
            missed = days_passed - last_sent
            print(f"У користувача {user_id} пропуски. Відправляємо повідомлення.")
            await bot.send_message(user_id, f"📌 У тебе {missed} пропуск(ів). Хочеш надолужити?")

@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id

    if data.startswith("complete:"):
        day = int(data.split(":")[1])
        mark_complete(user_id, day)
        await callback.message.edit_reply_markup()  # Прибрати кнопки
        await callback.answer("Завдання позначено як виконане ✅")

    elif data.startswith("incomplete:"):
        day = int(data.split(":")[1])
        mark_incomplete(user_id, day)
        await callback.message.edit_reply_markup()
        await callback.answer("Завдання позначено як НЕ виконане ❌")

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
    await bot.delete_webhook(drop_pending_updates=True)

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