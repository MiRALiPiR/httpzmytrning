import os
import logging
from telebot import TeleBot
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot_token = '7656738137:AAGahLO-G_TmYGlD6mx5ofgu1_5GZyKkrRo' # توکن ربات از فایل .env
INSTAGRAM_API_BASE_URL = "http://127.0.0.1:5000/api/instagram/download"  # آدرس API فلسک شما
API_KEY = "کلید دسترسی"

bot = TeleBot(bot_token)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "سلام! لطفاً لینک پست اینستاگرام را ارسال کنید.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    if "instagram.com" not in url:
        bot.reply_to(message, "❌ لطفاً یک لینک معتبر اینستاگرام ارسال کنید.")
        return

    try:
        bot.reply_to(message, "⏳ در حال پردازش لینک، لطفاً منتظر بمانید...")
        # درخواست به وب‌سرویس فلسک
        response = requests.get(INSTAGRAM_API_BASE_URL, params={"url": url, "key": API_KEY})
        response_data = response.json()

        if response.status_code == 200:
            download_url = response_data.get("download_url")
            if download_url:
                # دانلود فایل و ارسال به کاربر
                file_response = requests.get(download_url)
                bot.send_video(message.chat.id, file_response.content)
            else:
                bot.reply_to(message, "❌ لینک دانلود یافت نشد.")
        else:
            bot.reply_to(message, response_data.get("error", "❌ مشکلی پیش آمد."))
    except Exception as e:
        logger.error(f"Error handling Instagram link: {e}")
        bot.reply_to(message, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")

if __name__ == "__main__":
    bot.polling(none_stop=True)
