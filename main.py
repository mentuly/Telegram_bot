# from flask import Flask, request
# import telebot
# import os
# import requests

# TOKEN = os.getenv("BOT_TOKEN")
# WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# bot = telebot.TeleBot(TOKEN)
# app = Flask(__name__)

# @app.before_first_request
# def set_webhook():
#     webhook_url = f"{WEBHOOK_URL}"
#     response = WEBHOOK_URL = "https://web-production-8dd7d.up.railway.app/"


from flask import Flask, request
import telebot
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
WEBHOOK_URL = 'https://web-production-8dd7d.up.railway.app/'  # <- заміниш після деплою

app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Привіт!')

@bot.message_handler(content_types=['text'])
def get_txt_message(message):
    bot.send_message(message.from_user.id, message.text)

@app.route('/', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '!', 200

@app.route('/', methods=['GET'])
def index():
    return 'Бот працює!', 200

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))