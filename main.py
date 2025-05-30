import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, IS_TEST_MODE, SEND_TIME, TIMEZONE
from database import add_user, get_users, update_last_sent, mark_incomplete, mark_complete, get_incomplete_tasks, update_user_name, get_user_name, resume_user, suspend_user, delete_user, get_suspended_until, is_user_suspended
from lessons import lessons
from datetime import datetime, timezone

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InputMediaPhoto
from datetime import datetime, time, timedelta

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

class RegisterStates(StatesGroup):
    waiting_for_name = State()

class SuspendLessonStates(StatesGroup):
    waiting_for_suspend_choice = State()

media = [
    InputMediaPhoto(
        media='https://drive.google.com/uc?export=view&id=10Q7kBwFLpcNXdX58XsFioGfpwBLyKsnn'
    ),
    InputMediaPhoto(
        media='https://drive.google.com/uc?export=view&id=18QbZcCVfiGfJ613-kIHspQYZgDZSh57e',
        caption='Ця інструкція — як тепла підказка.\nВона допоможе почати. Продовжити. І не зникати, навіть якщо зник(-ла) на кілька днів.'
    ),
]

user_temp_messages = {}
user_suspend_messages = {}

@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    existing_users = [user[0] for user in get_users()]

    if user_id not in existing_users:
        add_user(user_id)
        await state.set_state(RegisterStates.waiting_for_name)
        await message.answer("Привіт! Як тебе звати? 🙂")
        return

    user_data = next((u for u in get_users() if u[0] == user_id), None)
    if user_data:
        suspended_until = user_data[3]
        if suspended_until is None or datetime.now() >= datetime.fromisoformat(suspended_until):
            user_name = get_user_name(user_id)
            if user_name:
                await send_intro_message(message, user_name)
            else:
                await state.set_state(RegisterStates.waiting_for_name)
                await message.answer("Привіт! Як тебе звати? ☺️")
        else:
            await message.answer(
                "У вас уже йде навчання. Якщо хочете призупинити його — натисніть /suspend_lesson ⏸️"
            )

@dp.message(RegisterStates.waiting_for_name)
async def handle_name_input(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.text.strip()
    update_user_name(user_id, user_name)

    await state.clear()
    await message.answer(f"Дякую, {user_name}! Раді знайомству 🚀")
    await bot.send_photo(
        chat_id=message.chat.id,
        photo='https://drive.google.com/uc?export=view&id=1wcsO799GbkFfDF3XrtRLijJWB_p3Eiua',
        caption='Дякуємо, що вибрав(-ла) нас.\nМи поряд — у кожному реченні, яке ти ще скажеш.\nКоманда Influbook 💛'
    )

    await bot.send_media_group(chat_id=message.chat.id, media=media)

    await send_intro_message(message, user_name)

async def send_intro_message(message: Message, user_name: str):
    sent_msg = await message.answer(
        text=(
            f"Ну що ж, {user_name} — момент настав.\n"
            "Перша сторінка вже чекає.\n"
            "Без ідеального настрою. Без очікувань.\n"
            "Просто ти, ручка і кілька слів англійською.\n\n"
            "Готовий(-а) почати прямо зараз?"
        ),
        reply_markup=start_keyboard().as_markup()
    )
    user_temp_messages[message.from_user.id] = sent_msg.message_id

def start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✍️ Так, поїхали!", callback_data="go_ahead")
    builder.button(text="🍵 Я ще з чаєм, настрій ловлю", callback_data="wait")
    builder.button(text="🙃 Не сьогодні, але я повернусь", callback_data="not_today")
    builder.adjust(1)
    return builder

# @dp.message(Command("delete"))
# async def delete_account_handler(message: Message):
#     user_id = message.from_user.id
#     delete_user(user_id)
#     await message.answer("Твій акаунт успішно видалено ✅")

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

@dp.message(Command("suspend_lesson"))
async def suspend_lesson_handler(message: Message):
    user_id = message.from_user.id
    users_data = get_users()
    user_data = next((u for u in users_data if u[0] == user_id), None)

    if not user_data:
        await message.answer("Користувача не знайдено.")
        return

    if user_data[3] == 1:
        text = "Бот вже призупинено. Можете продовжити, натиснувши кнопку нижче."
    else:
        suspend_user(user_id)
        text = "Бот призупинено. Коли будеш готовий(-а) повернутися, натисни кнопку нижче."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Продовжити", callback_data="resume_from_suspend")]
    ])
    sent_message = await message.answer(text, reply_markup=keyboard)

    if user_id not in user_suspend_messages:
        user_suspend_messages[user_id] = []
    user_suspend_messages[user_id].append(sent_message.message_id)

@dp.callback_query(F.data == "resume_from_suspend")
async def resume_from_suspend(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id in user_suspend_messages:
        for msg_id in user_suspend_messages[user_id]:
            try:
                await bot.delete_message(chat_id=user_id, message_id=msg_id)
            except:
                pass
        del user_suspend_messages[user_id]

    resume_user(user_id)
    users_data = get_users()
    user_data = next((u for u in users_data if u[0] == user_id), None)

    if not user_data:
        await callback.message.answer("Щось пішло не так, користувача не знайдено.")
        return

    last_sent = user_data[2]
    next_day = last_sent + 1
    if next_day >= len(lessons):
        await callback.message.answer("Ви завершили курс!")
        return

    text = lessons[next_day]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Завершено", callback_data=f"complete:{next_day}"),
         InlineKeyboardButton(text="❌ Не завершено", callback_data=f"incomplete:{next_day}")]
    ])
    await bot.send_message(user_id, f"\U0001F4DA {text}", reply_markup=keyboard)
    update_last_sent(user_id, next_day)
    await callback.answer("Продовжити ✅")

@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id

    if data.startswith("select_day:"):
        day = int(data.split(":")[1])
        text = f"\U0001F4CC День {day + 1}: {lessons[day]}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Виконано", callback_data=f"complete:{day}"),
            InlineKeyboardButton(text="❌ Все ще не виконано", callback_data=f"incomplete:{day}")
        ]])
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    elif data in ("wait", "not_today"):
        if user_id in user_temp_messages:
            try:
                await bot.delete_message(user_id, user_temp_messages[user_id])
            except:
                pass
            del user_temp_messages[user_id]

        text = (
            "Абсолютно окей. Influbook не тікає. Ми чекатимемо твій знак ☕️"
            if data == "wait" else
            "Головне — не зник назавжди. Коли захочеш — просто напиши “старт” і ми продовжимо з того, де ти зупинився(-лась) 🌙"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✍️ Так, поїхали!", callback_data="go_ahead")
        ]])

        sent_message = await callback.message.answer(text, reply_markup=keyboard)
        user_temp_messages[user_id] = sent_message.message_id
        await callback.answer()

    elif data == "go_ahead":
        if user_id in user_temp_messages:
            try:
                await bot.delete_message(user_id, user_temp_messages[user_id])
            except:
                pass
            del user_temp_messages[user_id]

        await callback.message.answer("Вау, клас! Перша сторінка — твоя. Let's begin. ✨")
        text = lessons[0]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Виконано", callback_data="complete:0"),
            InlineKeyboardButton(text="❌ Все ще не виконано", callback_data="incomplete:0")
        ]])
        await callback.message.answer(f"\U0001F4DA {text}", reply_markup=keyboard)
        await callback.answer()

    elif data.startswith("complete:"):
        day = int(data.split(":")[1])
        mark_complete(user_id, day)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🥳🥳🥳", callback_data="no_action")
        ]])
        await callback.message.edit_text(f"День {day + 1} позначено як виконане! 🎉", reply_markup=keyboard)
        await callback.answer("Завдання позначено як виконане ✅")

    elif data.startswith("incomplete:"):
        day = int(data.split(":")[1])
        mark_incomplete(user_id, day)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Виконано", callback_data=f"complete:{day}")
        ]])
        await callback.message.edit_text(f"День {day + 1} позначено як не виконане ❌", reply_markup=keyboard)
        await callback.answer("Завдання позначено як не виконане ❌")

    elif data == "no_action":
        await callback.answer()

    elif data == "resume_now":
        await callback.message.delete()
        resume_user(user_id)
        users_data = get_users()
        user_data = next((u for u in users_data if u[0] == user_id), None)
        if not user_data:
            await callback.message.answer("Щось пішло не так, користувача не знайдено.")
            return
        last_sent = user_data[2]
        next_day = last_sent + 1
        if next_day >= len(lessons):
            await callback.message.answer("Ви завершили курс!")
            return
        text = lessons[next_day]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Завершено", callback_data=f"complete:{next_day}"),
            InlineKeyboardButton(text="❌ Не завершено", callback_data=f"incomplete:{next_day}")
        ]])
        await bot.send_message(user_id, f"\U0001F4DA {text}", reply_markup=keyboard)
        update_last_sent(user_id, next_day)
        await callback.answer("Продовжено ✅")

    elif data == "resume_1100":
        await callback.message.delete()
        now = datetime.now()
        today_11am = datetime.combine(now.date(), time(11, 0))
        next_11am = today_11am + timedelta(days=1) if now >= today_11am else today_11am
        suspend_user(user_id, next_11am)
        await callback.answer(f"Буде автоматично відновлено о 11:00 ({next_11am.strftime('%H:%M')})")

def parse_suspended_until(suspended_until_str):
    if not suspended_until_str:
        return None
    dt = datetime.fromisoformat(suspended_until_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

async def send_lessons():
    users = get_users()

    now = datetime.now(timezone.utc).astimezone()
    print(f"Завдання відправлено в: {now}")

    if not users:
        print("Немає користувачів у базі даних!")
        return

    for user_id, start_date_str, last_sent, suspended_until in users:
        print(f"Перевіряємо користувача {user_id}: останній відправлений день - {last_sent}")

        suspend_date = parse_suspended_until(suspended_until)
        if suspend_date and now < suspend_date:
            print(f"Користувач {user_id} на паузі до {suspend_date}")
            continue

        start_date = datetime.fromisoformat(start_date_str)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)

        days_passed = (now.date() - start_date.date()).days
        print(f"Кількість пройдених днів: {days_passed}")

        if days_passed >= len(lessons):
            print(f"Курс завершено для користувача {user_id}.")
            continue

        if days_passed > last_sent or (days_passed == 0 and last_sent == 0):
            text = lessons[days_passed]
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[ 
                InlineKeyboardButton(text="✅ Завершено", callback_data=f"complete:{days_passed}"),
                InlineKeyboardButton(text="❌ Не завершено", callback_data=f"incomplete:{days_passed}")
            ]])

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