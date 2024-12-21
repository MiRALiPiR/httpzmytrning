import os
import telebot
from dotenv import load_dotenv
import logging

load_dotenv()
TOKEN = os.getenv('token')

if not TOKEN:
    raise ValueError("TOKEN نادرست است. اطمینان حاصل کنید که مقدار آن در فایل .env تعریف شده است.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TOKEN)

try:
    bot_info = bot.get_me()
    bot_username = bot_info.username
    logging.info(f'Bot Username: @{bot_username}')
except Exception as e:
    logger.error(f'Error fetching bot info: {str(e)}')
    
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////#

@bot.message_handler(commands=['start'])
def start(message):
    try:
        welcome_message = 'سلام! به ربات ما خوش آمدید!'
        bot.send_message(message.chat.id, welcome_message)
        
        user_id = message.from_user.id
        username = message.from_user.username or "Not Have"
        logging.info(f'User Info: id: {user_id} | username: {username} - Clicked start')

    except Exception as e:
        logger.error(f'Error in /start command: {str(e)}')

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
    لیست دستورات:
    /start - شروع استفاده از ربات
    /help - نمایش راهنما
    """
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.send_message(message.chat.id, 'پیام شما: ' + message.text)

if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f'Error on polling: {str(e)}')

bot.polling()