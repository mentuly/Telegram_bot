import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from pydub import AudioSegment
import speech_recognition as sr

TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = 'https://web-production-8dd7d.up.railway.app/'

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command('start'))
async def start(message: Message):
    await message.answer(
        "Привіт! Цей бот може:\n"
        "🔹 /voice_interpreter - перетворювати голосові повідомлення в текст\n"
        "🔹 /echo - повторювати ваші текстові повідомлення\n\n"
        "Оберіть потрібну функцію!"
    )

@dp.message(Command('voice_interpreter'))
async def voice_interpreter_mode(message: Message):
    await message.answer("🔊 Надішліть голосове повідомлення для розпізнавання.")

@dp.message(Command('echo'))
async def echo_mode(message: Message):
    await message.answer("🔄 Я повторю всі ваші повідомлення!")

@dp.message(lambda message: message.voice)
async def handle_voice(message: Message):
    file_info = await bot.get_file(message.voice.file_id)
    file_path = file_info.file_path
    downloaded_file = await bot.download_file(file_path)

    ogg_file = f"voice_{message.from_user.id}.ogg"
    wav_file = f"voice_{message.from_user.id}.wav"

    with open(ogg_file, 'wb') as f:
        f.write(downloaded_file.read())

    AudioSegment.from_file(ogg_file).export(wav_file, format="wav")

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_file) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio, language="uk-UA")
        await message.answer(f"📝 Розпізнаний текст:\n{text}")
    except sr.UnknownValueError:
        await message.answer("Не вдалося розпізнати голос.")
    except sr.RequestError as e:
        await message.answer(f"Помилка сервера: {e}")

    os.remove(ogg_file)
    os.remove(wav_file)

@dp.message(lambda message: message.text and not message.text.startswith('/'))
async def echo_message(message: Message):
    await message.answer(f"🔁 Ви сказали: {message.text}")

async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()

async def index(request):
    return web.Response(text="Бот працює!", status=200)

app = web.Application()
app.router.add_get("/", index)

SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/")
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))