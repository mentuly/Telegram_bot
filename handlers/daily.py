import json
import datetime
from aiogram import types, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data import users

def get_today_content():
    with open("data/content.json", "r", encoding="utf-8") as f:
        content = json.load(f)
    weekday = datetime.datetime.utcnow().strftime("%A").lower()
    return content.get(weekday)

async def send_daily_message(bot, user_id):
    data = get_today_content()
    if not data:
        return
    text = f"🗓 *{data['day'].capitalize()} — {data['topic']}*\n" \
           f"[Перейти до контенту]({data['link']})\n\n" \
           f"_Listen & then open your Influbook to reflect_"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Відкрити контент", url=data["link"])]
        ]
    )

    await bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)

def register_handlers(dp: Dispatcher):
    @dp.message(CommandStart())
    async def cmd_start(message: types.Message):
        user_id = message.from_user.id
        if users.add_user(user_id):
            from scheduler import setup_scheduler
            setup_scheduler(message.bot, user_id)
            await send_daily_message(message.bot, user_id)
            await message.answer("✅ Ви успішно зареєстровані! Щоденні повідомлення надсилатимуться автоматично.")
        else:
            await message.answer("🔔 Ви вже зареєстровані.")