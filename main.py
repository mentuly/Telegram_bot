from flask import Flask, request
import telebot
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('https://api.telegram.org/bot7030634417:AAH8AARR1ARkOGMe2mhRiI7TKABH8Yn0Pzc/setWebhook?url=https://your-app-name.up.railway.app/', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return 'OK', 200

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привіт! Я бот на Railway!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.send_message(message.chat.id, message.text)

if __name__ == '__main__':
    app.run()