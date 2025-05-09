import json
import datetime
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pathlib import Path

DATA_FILE = Path("data/content.json")


def get_today_content():
    weekday = datetime.datetime.now().strftime("%A")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        for entry in data:
            if entry["day"] == weekday:
                return entry
    return None


async def send_daily_message(bot: Bot, user_id: int):
    content = get_today_content()
    if not content:
        return

    day = content["day"]
    topic = content["topic"]
    link = content["link"]
    content_type = content["type"]

    text = (
        f"📅 *{day}*\n"
        f"🧠 *Topic:* {topic}\n\n"
        f"🎧 *{content_type.capitalize()}:* [Open]({link})\n\n"
        f"✨ _Reflect: Open your Influbook and write your thoughts._"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Open Resource", url=link)]
    ])

    await bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard, parse_mode="Markdown")