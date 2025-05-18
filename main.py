import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, IS_TEST_MODE, SEND_TIME, TIMEZONE
from database import add_user, get_users, update_last_sent, mark_incomplete, mark_complete, get_incomplete_tasks
from lessons import lessons
from datetime import datetime

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

@dp.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    existing_users = [user[0] for user in get_users()]
    if user_id in existing_users:
        await message.answer("Ви вже приєднані до курсу! ✅\nОчікуйте наступне завдання щодня або скористайтесь /complete_task")
    else:
        add_user(user_id)
        await message.answer("Привіт! Починаємо твій 30-денний курс навчання 🧠")

@dp.message(Command("complete_task"))
async def complete_task_handler(message: Message):
    user_id = message.from_user.id
    incomplete_days = get_incomplete_tasks(user_id)

    if not incomplete_days:
        await message.answer("У тебе немає невиконаних завдань 🎉")
        return

    buttons = [
        [InlineKeyboardButton(text=f"День {day + 1}", callback_data=f"select_day:{day}")]
        for day in incomplete_days
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Оберіть завдання, яке хочете позначити:", reply_markup=keyboard)

@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id

    if data.startswith("select_day:"):
        day = int(data.split(":")[1])
        text = f"\U0001F4CC День {day + 1}: {lessons[day]}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Завершено", callback_data=f"complete:{day}"),
             InlineKeyboardButton(text="❌ Все ще не завершено", callback_data=f"incomplete:{day}")]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    elif data.startswith("complete:"):
        day = int(data.split(":")[1])
        mark_complete(user_id, day)
        await callback.message.edit_reply_markup()
        await callback.answer("Завдання позначено як виконане ✅")

    elif data.startswith("incomplete:"):
        day = int(data.split(":")[1])
        mark_incomplete(user_id, day)
        await callback.message.edit_reply_markup()
        await callback.answer("Завдання позначено як НЕ виконане ❌")

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

            await bot.send_message(user_id, f"\U0001F4DA {text}", reply_markup=keyboard)
            update_last_sent(user_id, days_passed)
            print(f"Оновлено останній день для користувача {user_id} на {days_passed}")

            incomplete_days = get_incomplete_tasks(user_id)
            if incomplete_days:
                msg = "\U0001F4CC У тебе залишились незавершені дні:\n"
                for day in incomplete_days:
                    msg += f"- День {day + 1}: {lessons[day]}\n"
                msg += "\nВикористай /complete_task щоб позначити виконані ✅"
                await bot.send_message(user_id, msg)

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

if __name__ == "__main__":
    asyncio.run(start_bot())