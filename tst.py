import logging
import os
import random
import sqlite3
import string
import threading
import time

import telebot
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("token")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is not set in the .env file.")

bot = telebot.TeleBot(BOT_TOKEN)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    bot_info = bot.get_me()
    bot_username = bot_info.username
    logging.info(f'Bot Username: @{bot_username}')
except Exception as e:
    logger.error(f'Error fetching bot info: {str(e)}')

# Admin ID
ADMIN_ID = 6087657605
bot_name= 'اپلودر موقت'

# Channels
CHANNELS = [
    {"channel_number": "اول", "channel_name": "MiRALi ViBE", "username": "mirali_vibe", "invite_link": "https://t.me/+GrBtMvoIEJxjMGFk"},
    {"channel_number": "دوم", "channel_name": "SHADOW R3", "username": "shadow_r3", "invite_link": "https://t.me/+MfS2jBXEQg05MTRk"},
]

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Initialization
bot = TeleBot(BOT_TOKEN)

# Database
DB_PATH = "telegram_bot.db"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS start_links (
            start_link TEXT PRIMARY KEY,
            file_id TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_format TEXT NOT NULL,
            file_id TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Check user subscription
def get_channels_user_is_not_in(user_id):
    not_in_channels = []
    for channel in CHANNELS:
        try:
            status = bot.get_chat_member(f"@{channel['username']}", user_id).status
            if status in ["left", "kicked"]:
                not_in_channels.append(channel)
        except Exception as e:
            logger.error(f"Error checking user in channel {channel['username']}: {e}")
            not_in_channels.append(channel)
    return not_in_channels

# Send join prompt
def send_join_prompt(chat_id, missing_channels, message_id=None):
    markup = InlineKeyboardMarkup()
    for channel in missing_channels:
        markup.add(InlineKeyboardButton(f"عضویت در کانال {channel['channel_number']}", url=channel["invite_link"]))
    markup.add(InlineKeyboardButton("عضو شدم ✅", callback_data="check_join"))
    message_text = "❌ برای استفاده از ربات، ابتدا باید در کانال‌های زیر عضو شوید:"
    if message_id:
        bot.edit_message_text(message_text, chat_id, message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, message_text, reply_markup=markup)

# Handle missing channels
def handle_missing_channels(chat_id, user_id, message_id=None):
    missing_channels = get_channels_user_is_not_in(user_id)
    if missing_channels:
        send_join_prompt(chat_id, missing_channels, message_id)
        return True
    return False

# Generate start link
def generate_start_link():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# Add start link
def add_start_link(file_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT start_link FROM start_links WHERE file_id = ?", (file_id,))
        result = cursor.fetchone()
        if result:
            conn.close()
            return result[0]

        start_link = generate_start_link()
        cursor.execute("INSERT INTO start_links (start_link, file_id) VALUES (?, ?)", (start_link, file_id))
        conn.commit()
        conn.close()
        return start_link
    except Exception as e:
        logger.error(f"Error adding start link: {e}")
        raise

# Save file metadata to database
def save_file_metadata(file_name, file_format, file_id):
    try:
        if not file_name:  # If the file doesn't have a name, use a default name
            file_name = "untitled_file"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (file_name, file_format, file_id) VALUES (?, ?, ?)",
            (file_name, file_format, file_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving file metadata: {e}")
        raise

@bot.message_handler(commands=["get_id"])
def handle_get_id(message):
    try:
        if handle_missing_channels(message.chat.id, message.from_user.id):
            return
        # اطلاعات کاربر
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        username = f"@{message.from_user.username}" if message.from_user.username else None

        # ساخت پیام پاسخ
        response = []
        if first_name:
            response.append(f"👤 First Name: {first_name}")
        if last_name:
            response.append(f"👥 Last Name: {last_name}")
        if username:
            response.append(f"🔗 Username: {username}")
        response.append(f"🆔 User ID: <code>{user_id}</code>")

        # ارسال پیام
        bot.reply_to(message, "\n".join(response), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in handle_get_id: {e}")
        bot.reply_to(message, "❌ خطایی رخ داد.")

@bot.message_handler(commands=["custom_id"])
def handle_get_custom_id(message):
    try:
        # از کاربر می‌خواهد لینک یا یوزرنیم کانال/گروه را ارسال کند
        bot.reply_to(
            message,
            "📎 لطفاً یوزرنیم کانال یا گروه مورد نظر را ارسال کنید\n"
            "🟢 مثال: @example_channel\n\n"
            "⚠️ توجه ⚠️\n"
            "🔴 شما نمیتوانید آیدی عددی کانال های خصوصی را دریافت کنید !"
        )
        # وارد حالت انتظار برای دریافت پیام بعدی از کاربر
        bot.register_next_step_handler(message, fetch_custom_id)
    except Exception as e:
        logger.error(f"Error in handle_get_custom_id: {e}")
        bot.reply_to(message, "❌ خطایی رخ داد.")

def fetch_custom_id(message):
    try:
        # گرفتن لینک یا یوزرنیم ارسال‌شده
        input_text = message.text.strip()

        # بررسی یوزرنیم یا لینک
        if not input_text.startswith("@") and "t.me/" not in input_text:
            bot.reply_to(message, "⚠️ یوزرنیم ارسالی شما معتبر نیست\n\n🔰 برای استفاده مجدد از این بخش دستور /getcustomid را بفرستید🌹")
            return

        # حذف بخش اضافی لینک (اگر لینک است)
        if "t.me/" in input_text:
            input_text = input_text.split("t.me/")[-1].strip()

        # گرفتن اطلاعات کانال/گروه
        chat = bot.get_chat(input_text)
        chat_id = chat.id

        # ارسال آیدی عددی به کاربر
        bot.reply_to(
            message,
            f"✅ آیدی عددی کانال/گروه:\n<code>{chat_id}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in fetch_custom_id: {e}")
        bot.reply_to(message, "❌ خطایی رخ داد. مطمئن شوید یوزرنیم معتبر وارد کرده‌اید.")

@bot.message_handler(commands=["contact"])
def handle_contact_command(message):
    try:
        # از کاربر می‌خواهد آیدی عددی فرد موردنظر را ارسال کند
        bot.reply_to(
            message,
            "📎 لطفاً آیدی عددی فرد موردنظر را ارسال کنید (مثال: 123456789)."
        )
        # وارد حالت انتظار برای دریافت پیام بعدی از کاربر
        bot.register_next_step_handler(message, fetch_contact_info)
    except Exception as e:
        logger.error(f"Error in handle_contact_command: {e}")
        bot.reply_to(message, "❌ خطایی رخ داد.")

def fetch_contact_info(message):
    try:
        # بررسی ورودی کاربر
        user_id_text = message.text.strip()
        if not user_id_text.isdigit():
            bot.reply_to(message, "❌ لطفاً یک آیدی عددی معتبر وارد کنید.")
            return

        user_id = int(user_id_text)

        # دریافت اطلاعات کاربر
        user_chat = bot.get_chat(user_id)

        # بررسی یوزرنیم
        if user_chat.username:
            contact_link = f"https://t.me/{user_chat.username}"
            response = f"✅ پیوی کاربر:\n<a href='{contact_link}'>{contact_link}</a>"
        else:
            # اگر یوزرنیم نداشت، لینک پیوی با استفاده از آیدی عددی ایجاد می‌شود
            contact_link = f"https://t.me/c/{user_id}"
            response = (
                f"❗️ این کاربر یوزرنیم ندارد.\n"
                f"✅ لینک پیوی با استفاده از آیدی عددی:\n<a href='{contact_link}'>{contact_link}</a>"
            )

        bot.reply_to(message, response, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in fetch_contact_info: {e}")
        bot.reply_to(message, "❌ خطایی رخ داد. مطمئن شوید آیدی عددی معتبر وارد کرده‌اید.")

@bot.message_handler(commands=["load_file"])
def handle_loadfile_command(message):
    try:
        bot.reply_to(message, "📎 لطفاً فایل موردنظر خود را ارسال کنید.")
        # وارد حالت انتظار برای دریافت فایل
        bot.register_next_step_handler(message, process_uploaded_file)
    except Exception as e:
        logger.error(f"Error in handle_loadfile_command: {e}")
        bot.reply_to(message, "❌ خطایی رخ داد.")

def process_uploaded_file(message):
    try:
        # بررسی نوع فایل و استخراج file_id
        file_id = None

        if message.content_type == "photo":
            file_id = message.photo[-1].file_id
        elif message.content_type in ["video", "document", "audio", "voice", "sticker", "animation"]:
            file_id = getattr(message, message.content_type).file_id

        if not file_id:
            bot.reply_to(message, "❌ فایل معتبر ارسال نشده است. لطفاً دوباره تلاش کنید.")
            return

        bot.reply_to(message, f"✅ فایل شما دریافت شد.\n\n📂 File ID:\n<code>{file_id}</code>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in process_uploaded_file: {e}")
        bot.reply_to(message, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")

@bot.message_handler(commands=["get_file"])
def handle_getfile_command(message):
    """
    دستور /getfile: درخواست فایل آیدی از کاربر.
    """
    try:
        # درخواست فایل آیدی از کاربر
        bot.reply_to(message, "📎 لطفاً فایل آیدی موردنظر خود را ارسال کنید.")
        # وارد حالت انتظار برای دریافت فایل آیدی
        bot.register_next_step_handler(message, send_file_by_id)
    except Exception as e:
        logger.error(f"Error in handle_getfile_command: {e}")
        bot.reply_to(message, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")

def send_file_by_id(message):
    """
    ارسال فایل با استفاده از فایل آیدی.
    """
    try:
        # گرفتن فایل آیدی از پیام
        file_id = message.text.strip()

        if not file_id:
            bot.reply_to(message, "❌ لطفاً یک فایل آیدی معتبر وارد کنید.")
            return

        # تلاش برای ارسال فایل
        bot.send_document(message.chat.id, file_id)
        bot.reply_to(message, "✅ فایل ارسال شد.")
    except telebot.apihelper.ApiException as api_error:
        # مدیریت خطاهای مربوط به API تلگرام
        if "Bad Request: file_id is empty" in str(api_error):
            bot.reply_to(message, "❌ فایل آیدی ارسال‌شده خالی است. لطفاً فایل آیدی معتبر ارسال کنید.")
        elif "Bad Request: wrong file identifier" in str(api_error):
            bot.reply_to(message, "❌ فایل آیدی اشتباه است. لطفاً فایل آیدی را بررسی کنید.")
        elif "Bad Request: file not found" in str(api_error):
            bot.reply_to(message, "❌ فایل آیدی یافت نشد. مطمئن شوید فایل آیدی درست است.")
        else:
            logger.error(f"API Error in send_file_by_id: {api_error}")
            bot.reply_to(message, "❌ خطایی در ارسال فایل رخ داد.")
    except Exception as e:
        # مدیریت سایر خطاها
        logger.error(f"Error in send_file_by_id: {e}")
        bot.reply_to(message, "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")


@bot.message_handler(content_types=["photo", "video", "document", "audio", "voice", "sticker", "animation"])
def handle_document(message):
    try:
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "❌ فقط ادمین می‌تواند فایل ارسال کند.")
            return

        file_id = None
        file_name = None
        file_format = None

        # Determine file type and name
        if message.content_type == "photo":
            try:
                # انتخاب عکس بزرگ‌تر
                file_id = message.photo[-1].file_id
                file_name = f"photo_{file_id}"  # نام پیش‌فرض
                file_format = "photo"
            except IndexError:
                bot.reply_to(message, "❌ خطا در پردازش عکس. لطفاً دوباره تلاش کنید.")
                return
        elif message.content_type == "video":
            file = message.video
            file_id = file.file_id
            file_name = file.file_name if hasattr(file, "file_name") else "video_without_name"
            file_format = "video"
        elif message.content_type == "document":
            file = message.document
            file_id = file.file_id
            file_name = file.file_name if hasattr(file, "file_name") else "document_without_name"
            file_format = "document"
        elif message.content_type == "audio":
            file = message.audio
            file_id = file.file_id
            file_name = file.file_name if hasattr(file, "file_name") else "audio_without_name"
            file_format = "audio"
        elif message.content_type == "voice":
            file = message.voice
            file_id = file.file_id
            file_name = "voice_note"
            file_format = "voice"
        elif message.content_type == "sticker":
            file = message.sticker
            file_id = file.file_id
            file_name = "sticker"
            file_format = "sticker"
        elif message.content_type == "animation":
            file = message.animation
            file_id = file.file_id
            file_name = "animation"
            file_format = "animation"

        # Check if file_id is valid
        if not file_id:
            bot.reply_to(message, "❌ این نوع فایل پشتیبانی نمی‌شود.")
            return

        # Generate a start link for the file
        start_link = add_start_link(file_id)
        start_url = f"https://t.me/{bot.get_me().username}?start={start_link}"

        # Save the file metadata to the database
        save_file_metadata(file_name, file_format, file_id)

        bot.reply_to(
            message,
            f"✅ فایل شما ذخیره شد. برای دسترسی به فایل، از لینک زیر استفاده کنید:\n\n"
            f"{start_url}",
            reply_markup=None,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error handling document: {e}")
        bot.send_message(message.chat.id, "❌ خطایی رخ داد.")

# Handle start command
@bot.message_handler(commands=["start"])
def handle_start_link(message):
    try:
        if handle_missing_channels(message.chat.id, message.from_user.id):
            return

        parts = message.text.split(" ")
        if len(parts) < 2 or not parts[1].isalnum():
            bot.reply_to(message, f"به ربات {bot_name} خوش اومدید!")
            return

        start_link = parts[1]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT file_id FROM start_links WHERE start_link = ?", (start_link,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            bot.reply_to(message, f"به ربات {bot_name} خوش اومدید!")
            return

        file_id = result[0]
        bot.send_document(
            message.chat.id,
            file_id,
            caption="""این فایل و ربات 
            توسط مجموعه @MiRALi_SHOP_OG ساخته شده
            """
        )
    except Exception as e:
        logger.error(f"Error handling start command: {e}")
        bot.reply_to(message, "❌ خطایی رخ داد.")

# Handle help command
@bot.message_handler(commands=["help"])
def handle_help(message):
    help_text = (
        "🤖 راهنمای استفاده از ربات:\n\n"
        "1️⃣ برای دریافت فایل‌ها باید ابتدا در کانال‌های مشخص شده عضو شوید.\n"
        "2️⃣ پس از عضویت، از دکمه 'عضو شدم ✅' استفاده کنید تا عضویت شما تأیید شود.\n"
        "3️⃣ فایل‌ها را می‌توانید از طریق لینک استارت اختصاصی دریافت کنید.\n"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['giveme11228'])
def sendata(message):
    database = '/home/miraliofficial/telegram_bot.db'
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ فقط ادمین می‌تواند فایل ارسال کند.")
        return
    if os.path.exists(database):
        with open(database, 'rb') as db_file:
            bot.send_document(message.chat.id, db_file)
    else:
        bot.reply_to(message, "❌ فایل پایگاه داده پیدا نشد.")

# Handle join confirmation callback
@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def handle_check_join(call: CallbackQuery):
    try:
        if not handle_missing_channels(call.message.chat.id, call.from_user.id, call.message.message_id):
            bot.edit_message_text("✅ عضویت شما تأیید شد! اکنون می‌توانید از ربات استفاده کنید.", call.message.chat.id, call.message.message_id)
    except Exception as e:
        logger.error(f"Error in handle_check_join: {e}")
        bot.send_message(call.message.chat.id, "❌ خطایی رخ داد.")

# Initialize database
initialize_db()

# Polling
if __name__ == "__main__":
    logger.info("Bot is running...")
    bot.infinity_polling()