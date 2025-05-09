import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.markdown import hbold
from datetime import datetime, timedelta


TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=TOKEN)
    
dp = Dispatcher()

DAILY_CONTENT = {
    1: {
        "title": "Mindful Listening",
        "link": "https://example.com/day1.mp3"
    },
    2: {
        "title": "Vocabulary Expansion",
        "link": "https://example.com/day2.mp4"
    },
}

user_progress = {}

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    user_progress[message.from_user.id] = {"current_day": 1, "last_seen": datetime.now()}
    await message.answer("👋 Welcome to Influbook bot! Let's start your English journey.")
    await send_daily_content(message.from_user.id)

async def send_daily_content(user_id):
    day = user_progress.get(user_id, {}).get("current_day", 1)
    content = DAILY_CONTENT.get(day)

    if not content:
        await bot.send_message(user_id, "🎉 You've completed all available content! Stay tuned for more.")
        return

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Mark Day {day} as complete ✅", callback_data=f"complete:{day}")]
    ])

    text = f"<b>Day {day}</b> - {content['title']}\
\n🎧 {content['link']}\n\nListen & then open your Influbook to reflect."
    await bot.send_message(user_id, text, reply_markup=markup)

@dp.callback_query(F.data.startswith("complete:"))
async def mark_complete(callback: CallbackQuery):
    day = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    user_progress[user_id]["current_day"] = day + 1
    user_progress[user_id]["last_seen"] = datetime.now()
    await callback.message.edit_text(callback.message.text + "\n\n✅ Marked as complete!")

@dp.message(F.text.lower().contains("english"))
async def evening_reflection(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Done", callback_data="reflect_done")
    builder.button(text="📝 Write more", callback_data="reflect_more")
    await message.answer("How was your English today? Just one sentence:", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "reflect_done")
async def reflect_done(callback: CallbackQuery):
    await callback.message.edit_text("✅ Thanks for reflecting! See you tomorrow.")

@dp.callback_query(F.data == "reflect_more")
async def reflect_more(callback: CallbackQuery):
    await callback.message.edit_text("📝 Feel free to write more and share it with us later!")

async def missed_day_reminder():
    while True:
        for user_id, data in user_progress.items():
            if datetime.now() - data["last_seen"] > timedelta(days=2):
                await bot.send_message(user_id,
                    "Missed a day? No worries – let’s continue.\nTap below to resume from your last page.",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[[InlineKeyboardButton(text="📖 Resume", callback_data="resume")]]
                    )
                )
        await asyncio.sleep(86400)

@dp.callback_query(F.data == "resume")
async def resume_content(callback: CallbackQuery):
    await send_daily_content(callback.from_user.id)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())