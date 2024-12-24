# import os
# import logging
# import requests
# from dotenv import load_dotenv
# import telebot

# load_dotenv()

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# BOT_TOKEN = os.getenv("token")
# HAJI_API_KEY = os.getenv("HAJI_API_KEY")  # کلید API خود را در فایل .env ذخیره کنید

# bot = telebot.TeleBot(BOT_TOKEN)

# def fetch_instagram_media(url: str) -> str:
#     try:
#         api_url = f"https://api3.haji-api.ir/sub/insta/auto?url={url}&key={HAJI_API_KEY}"
#         response = requests.get(api_url)
#         response_data = response.json()

#         if response.status_code == 200 and response_data.get("status") == "success":
#             return response_data.get("download_url")
#         else:
#             logger.error(f"API Error: {response_data.get('message', 'Unknown error')}")
#             raise ValueError(response_data.get("message", "مشکلی در ارتباط با API وجود دارد."))
#     except Exception as e:
#         logger.error(f"Error fetching media from API: {e}")
#         raise

# @bot.message_handler(commands=['start'])
# def start(message):
#     bot.reply_to(message, "سلام! لطفاً لینک ویدیو یا پست اینستاگرام را ارسال کنید.")

# @bot.message_handler(commands=['help'])
# def send_help(message):
#     help_text = """
#     🌟 **راهنمای دانلود اینستاگرام** 🌟

#     1️⃣ لینک ویدیو، پست، استوری یا پروفایل اینستاگرام را ارسال کنید.
#     2️⃣ ربات فایل مربوطه را برای شما دانلود و ارسال می‌کند.

#     **توجه:** تنها لینک‌های معتبر اینستاگرام قابل پردازش هستند.
#     """
#     bot.reply_to(message, help_text, parse_mode="Markdown")

# @bot.message_handler(func=lambda message: True)
# def handle_message(message):
#     url = message.text.strip()
#     if "instagram.com" in url:
#         try:
#             bot.reply_to(message, "⏳ در حال دریافت اطلاعات... لطفاً منتظر بمانید.")
            
#             # دریافت لینک دانلود از API
#             download_url = fetch_instagram_media(url)
            
#             if download_url:
#                 bot.reply_to(message, "✅ فایل آماده است. در حال ارسال...")
#                 file_response = requests.get(download_url)
                
#                 # ذخیره فایل به صورت موقت
#                 file_name = "downloaded_instagram_file.mp4"
#                 with open(file_name, "wb") as f:
#                     f.write(file_response.content)
                
#                 # ارسال فایل به کاربر
#                 with open(file_name, "rb") as video:
#                     bot.send_video(message.chat.id, video)
                
#                 # حذف فایل موقت
#                 os.remove(file_name)
#             else:
#                 bot.reply_to(message, "❌ فایل قابل دانلود نیست.")
#         except ValueError as ve:
#             bot.reply_to(message, f"❌ {ve}")
#         except Exception as e:
#             logger.error(f"Error handling message: {e}")
#             bot.reply_to(message, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
#     else:
#         bot.reply_to(message, "❌ لطفاً لینک معتبر اینستاگرام ارسال کنید.")

# if __name__ == "__main__":
#     bot.polling(none_stop=True)















from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Welcome to Instagram Downloader API!"})

@app.route('/api/instagram/download', methods=['GET'])
def instagram_download():
    url = request.args.get('url')
    key = request.args.get('key')

    # اعتبارسنجی پارامترها
    if not url or not key:
        return jsonify({"error": "پارامترهای url و key ضروری هستند."}), 400

    # فراخوانی API خارجی
    haji_api_url = f"https://api3.haji-api.ir/sub/insta/auto?url={url}&key={key}"
    try:
        response = requests.get(haji_api_url)
        response_data = response.json()

        if response.status_code == 200 and response_data.get("status") == "success":
            return jsonify({"download_url": response_data.get("download_url")})
        else:
            return jsonify({"error": response_data.get("message", "مشکلی پیش آمد.")}), 400
    except Exception as e:
        return jsonify({"error": f"خطایی رخ داد: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)