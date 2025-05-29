import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, IS_TEST_MODE, SEND_TIME, TIMEZONE
from database import add_user, get_users, update_last_sent, mark_incomplete, mark_complete, get_incomplete_tasks, update_user_name, get_user_name, delete_user
from lessons import lessons
from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InputFile

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

class RegisterStates(StatesGroup):
    waiting_for_name = State()

@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    existing_users = [user[0] for user in get_users()]

    if user_id not in existing_users:
        add_user(user_id)
        await state.set_state(RegisterStates.waiting_for_name)
        await message.answer("Привіт! Як тебе називати? 🙂")
    else:
        user_name = get_user_name(user_id)
        if user_name:
            await send_intro_message(message, user_name)
        else:
            await state.set_state(RegisterStates.waiting_for_name)
            await message.answer("Привіт! Як тебе називати? 🙂")

@dp.message(RegisterStates.waiting_for_name)
async def handle_name_input(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.text.strip()
    update_user_name(user_id, user_name)

    await state.clear()
    await message.answer(f"Дякую, {user_name}! Радіймо знайомству 🚀")
    await send_intro_message(message, user_name)

async def send_intro_message(message: Message, user_name: str):
    await message.answer(
        text=(
            f"Ну що ж, {user_name} — момент настав.\n"
            "Перша сторінка вже чекає.\n"
            "Без ідеального настрою. Без очікувань.\n"
            "Просто ти, ручка і кілька слів англійською.\n\n"
            "Готовий(-а) почати прямо зараз?"
        ),
        reply_markup=start_keyboard().as_markup()
    )

def start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✍️ Так, поїхали!", callback_data="go_ahead")
    builder.button(text="🍵 Я ще з чаєм, настрій ловлю", callback_data="wait")
    builder.button(text="🙃 Не сьогодні, але я повернусь", callback_data="not_today")
    builder.adjust(1)
    return builder

@dp.message(Command("delete"))
async def delete_account_handler(message: Message):
    user_id = message.from_user.id
    delete_user(user_id)
    await message.answer("Твій акаунт успішно видалено ✅")

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

    elif data == "go_ahead":
        await callback.message.answer("Вау, клас! Перша сторінка — твоя. Let's begin. ✨")
        text = lessons[0]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Завершено", callback_data="complete:0"),
             InlineKeyboardButton(text="❌ Все ще не завершено", callback_data="incomplete:0")]
        ])
        await callback.message.answer(f"\U0001F4DA {text}", reply_markup=keyboard)
        await callback.answer()

    elif data == "wait":
        await callback.message.answer("Абсолютно окей. Influbook не тікає. Ми чекатимемо твій знак ☕️")
        await callback.answer()

    elif data == "not_today":
        await callback.message.answer("Головне — не зник назавжди. Коли захочеш — просто напиши “старт” і ми продовжимо з того, де ти зупинився(-лась) 🌙")
        await callback.answer()

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