import logging
import os
import random
import sqlite3
import string
import time
import uuid

from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("bot_token")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is not set in the .env file.")

ADMIN_ID = 6087657605
bot_name = 'Uploader Mirali'

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Initialization
bot = TeleBot(BOT_TOKEN)

# Database setup
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
        CREATE TABLE IF NOT EXISTS mandatory_channels (
            channel_number TEXT, 
            channel_name TEXT, 
            username TEXT, 
            invite_link TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            file_id TEXT PRIMARY KEY, 
            file_name TEXT NOT NULL DEFAULT 'unknown_file', 
            file_format TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_mandatory_channel(channel_number, channel_name, username, invite_link):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mandatory_channels (channel_number, channel_name, username, invite_link) VALUES (?, ?, ?, ?)",
                   (channel_number, channel_name, username, invite_link))
    conn.commit()
    conn.close()

def get_channels():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mandatory_channels")
    channels = cursor.fetchall()
    conn.close()
    return [{"channel_number": c[0], "channel_name": c[1], "username": c[2], "invite_link": c[3]} for c in channels]

def get_channels_user_is_not_in(user_id):
    not_in_channels = []
    for channel in get_channels():
        try:
            status = bot.get_chat_member(f"@{channel['username']}", user_id).status
            if status in ["left", "kicked"]:
                not_in_channels.append(channel)
        except Exception as e:
            logger.error(f"Error checking user in channel {channel['username']}: {e}")
            not_in_channels.append(channel)
    return not_in_channels

def is_user_in_channels(user_id):
    return not bool(get_channels_user_is_not_in(user_id))

def generate_start_link():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def add_start_link(file_id):
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

def save_file_metadata(file_name, file_format, file_id):
    if not file_name:
        raise ValueError("File name cannot be empty or None.")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO files (file_id, file_name, file_format) VALUES (?, ?, ?)",
            (file_id, file_name, file_format),
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"❌ خطا در ذخیره فایل: {str(e)}")
        raise e
    finally:
        conn.close()


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

def handle_missing_channels(chat_id, user_id, message_id=None):
    missing_channels = get_channels_user_is_not_in(user_id)
    if missing_channels:
        send_join_prompt(chat_id, missing_channels, message_id)
        return True
    return False

@bot.message_handler(commands=["start"])
def handle_start(message):
    # همواره درخواست عضویت ارسال شود
    send_join_prompt(message.chat.id, get_channels())

    # اگر لینک فایل ارسال شده باشد، آن را بررسی می‌کنیم
    start_link = message.text.split(" ")[1] if len(message.text.split()) > 1 else None
    if not start_link:
        bot.reply_to(message, f"به ربات {bot_name} خوش آمدید!")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_id FROM start_links WHERE start_link = ?", (start_link,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        bot.reply_to(message, "❌ لینک نامعتبر است یا فایل حذف شده است.")
        return

    bot.send_document(message.chat.id, result[0], caption="فایل توسط ربات ارسال شد: @mirali_official")


@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def handle_check_join(call):
    # بررسی عضویت کاربر در کانال‌های اجباری
    if not handle_missing_channels(call.message.chat.id, call.from_user.id, call.message.message_id):
        bot.edit_message_text("✅ عضویت شما تأیید شد! اکنون می‌توانید از ربات استفاده کنید.", call.message.chat.id, call.message.message_id)

#/////////////////////////////////////////////////////////////////////////////////////////////////////
# @bot.message_handler(commands=["manage"])
# def manage_channels(message):
#     if message.from_user.id != ADMIN_ID:
#         bot.reply_to(message, "❌ فقط ادمین می‌تواند به این پنل دسترسی داشته باشد.")
#         return

#     markup = InlineKeyboardMarkup()
#     markup.add(InlineKeyboardButton("➕ اضافه کردن کانال", callback_data="add_channel"))
#     markup.add(InlineKeyboardButton("➖ حذف کردن کانال", callback_data="remove_channel"))
#     markup.add(InlineKeyboardButton("📜 مشاهده لیست کانال‌ها", callback_data="list_channels"))
#     bot.reply_to(message, "🎛 پنل مدیریت کانال‌های اجباری:", reply_markup=markup)

# @bot.callback_query_handler(func=lambda call: call.data in ["add_channel", "remove_channel", "list_channels"])
# def handle_manage_channels(call):
#     if call.data == "add_channel":
#         bot.send_message(call.message.chat.id, "لطفاً شماره کانال را وارد کنید:")
#         bot.register_next_step_handler(call.message, get_channel_number)
#     elif call.data == "remove_channel":
#         channels = get_channels()
#         if not channels:
#             bot.send_message(call.message.chat.id, "❌ هیچ کانالی برای حذف وجود ندارد.")
#             return

#         response = "✅ لیست کانال‌های اجباری:\n\n"
#         for channel in channels:
#             response += f"📌 شماره: {channel['channel_number']}\n<b>{channel['channel_name']}</b>\n🔗 یوزرنیم: @{channel['username']}\n📥 لینک: {channel['invite_link']}\n\n"
#         bot.send_message(call.message.chat.id, response, parse_mode="HTML")
#         bot.send_message(call.message.chat.id, "شماره کانال موردنظر برای حذف را وارد کنید:")
#         bot.register_next_step_handler(call.message, process_remove_channel)
#     elif call.data == "list_channels":
#         channels = get_channels()
#         if not channels:
#             bot.send_message(call.message.chat.id, "❌ هیچ کانال اجباری‌ای ثبت نشده است.")
#             return

#         response = "✅ لیست کانال‌های اجباری:\n\n"
#         for channel in channels:
#             response += f"📌 شماره: {channel['channel_number']}\n<b>{channel['channel_name']}</b>\n🔗 یوزرنیم: @{channel['username']}\n📥 لینک: {channel['invite_link']}\n\n"
#         bot.send_message(call.message.chat.id, response, parse_mode="HTML")

# # مراحل اضافه کردن کانال
# def get_channel_number(message):
#     if message.from_user.id != ADMIN_ID:
#         bot.reply_to(message, "❌ فقط ادمین می‌تواند کانال اضافه کند.")
#         return

#     channel_number = message.text.strip()
#     bot.send_message(message.chat.id, "لطفاً نام کانال را وارد کنید:")
#     bot.register_next_step_handler(message, get_channel_name, channel_number)

# def get_channel_name(message, channel_number):
#     channel_name = message.text.strip()
#     bot.send_message(message.chat.id, "لطفاً یوزرنیم کانال (بدون @) را وارد کنید:")
#     bot.register_next_step_handler(message, get_channel_username, channel_number, channel_name)

# def get_channel_username(message, channel_number, channel_name):
#     username = message.text.strip().lstrip("@")
#     bot.send_message(message.chat.id, "لطفاً لینک دعوت کانال را وارد کنید:")
#     bot.register_next_step_handler(message, save_channel_info, channel_number, channel_name, username)

# def save_channel_info(message, channel_number, channel_name, username):
#     invite_link = message.text.strip()
#     try:
#         add_mandatory_channel(channel_number, channel_name, username, invite_link)
#         bot.send_message(message.chat.id, f"✅ کانال {channel_name} با موفقیت اضافه شد.")
#     except Exception as e:
#         logger.error(f"Error adding channel: {e}")
#         bot.send_message(message.chat.id, "❌ خطایی در اضافه کردن کانال رخ داد.")

# # حذف کانال با شماره کانال
# def process_remove_channel(message):
#     try:
#         if message.from_user.id != ADMIN_ID:
#             bot.reply_to(message, "❌ فقط ادمین می‌تواند کانال حذف کند.")
#             return

#         channel_number = message.text.strip()
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("DELETE FROM mandatory_channels WHERE channel_number = ?", (channel_number,))
#         conn.commit()
#         conn.close()

#         if cursor.rowcount > 0:
#             bot.reply_to(message, f"✅ کانال با شماره {channel_number} حذف شد.")
#         else:
#             bot.reply_to(message, "❌ کانالی با این شماره یافت نشد.")
#     except Exception as e:
#         logger.error(f"Error removing channel: {e}")
#         bot.reply_to(message, "❌ خطایی در حذف کانال رخ داد.")


@bot.message_handler(commands=["manage"])
def manage_channels(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ فقط ادمین می‌تواند به این پنل دسترسی داشته باشد.")
        return

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ اضافه کردن کانال", callback_data="add_channel"))
    markup.add(InlineKeyboardButton("➖ حذف کردن کانال", callback_data="remove_channel"))
    markup.add(InlineKeyboardButton("📜 مشاهده لیست کانال‌ها", callback_data="list_channels"))
    markup.add(InlineKeyboardButton("🗑 حذف تمام کانال‌ها", callback_data="delete_all_channels"))
    markup.add(InlineKeyboardButton("🚪 خروج", callback_data="close_manage_panel"))
    bot.send_message(message.chat.id, "🎛 پنل مدیریت کانال‌های اجباری:", reply_markup=markup)


# مدیریت دکمه‌های پنل
@bot.callback_query_handler(func=lambda call: call.data in ["add_channel", "remove_channel", "list_channels", "delete_all_channels", "close_manage_panel"])
def handle_manage_channels(call):
    if call.data == "add_channel":
        bot.send_message(call.message.chat.id, "➕ لطفاً شماره کانال را وارد کنید:")
        bot.register_next_step_handler(call.message, get_channel_number)

    elif call.data == "remove_channel":
        channels = get_channels()
        if not channels:
            bot.send_message(call.message.chat.id, "❌ هیچ کانالی برای حذف وجود ندارد.")
            return

        response = "✅ لیست کانال‌های اجباری:\n\n"
        for idx, channel in enumerate(channels, 1):
            response += f"{idx}. {channel['channel_name']} (#{channel['channel_number']})\n"
        response += "\nلطفاً شماره کانال موردنظر برای حذف را وارد کنید:"
        bot.send_message(call.message.chat.id, response)
        bot.register_next_step_handler(call.message, process_remove_channel)

    elif call.data == "list_channels":
        channels = get_channels()
        if not channels:
            bot.send_message(call.message.chat.id, "❌ هیچ کانال اجباری‌ای ثبت نشده است.")
            return

        response = "✅ لیست کانال‌های اجباری:\n\n"
        for idx, channel in enumerate(channels, 1):
            response += f"{idx}. {channel['channel_name']} (#{channel['channel_number']})\n🔗 لینک دعوت: {channel['invite_link']}\n\n"
        bot.send_message(call.message.chat.id, response)

    elif call.data == "delete_all_channels":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ تایید", callback_data="confirm_delete_all"))
        markup.add(InlineKeyboardButton("❌ لغو", callback_data="close_manage_panel"))
        bot.send_message(call.message.chat.id, "⚠️ آیا از حذف تمام کانال‌ها مطمئن هستید؟", reply_markup=markup)

    elif call.data == "close_manage_panel":
        bot.send_message(call.message.chat.id, "✅ پنل مدیریت بسته شد.")


# تایید حذف تمام کانال‌ها
@bot.callback_query_handler(func=lambda call: call.data == "confirm_delete_all")
def confirm_delete_all_channels(call):
    try:
        delete_all_channels()
        bot.send_message(call.message.chat.id, "✅ تمام کانال‌ها با موفقیت حذف شدند.")
    except Exception as e:
        logger.error(f"Error deleting all channels: {e}")
        bot.send_message(call.message.chat.id, "❌ خطایی در حذف تمام کانال‌ها رخ داد.")


# مراحل اضافه کردن کانال
def get_channel_number(message):
    channel_number = message.text.strip()
    bot.send_message(message.chat.id, "لطفاً نام کانال را وارد کنید:")
    bot.register_next_step_handler(message, get_channel_name, channel_number)


def get_channel_name(message, channel_number):
    channel_name = message.text.strip()
    bot.send_message(message.chat.id, "لطفاً یوزرنیم کانال (بدون @) را وارد کنید:")
    bot.register_next_step_handler(message, get_channel_username, channel_number, channel_name)


def get_channel_username(message, channel_number, channel_name):
    username = message.text.strip().lstrip("@")
    bot.send_message(message.chat.id, "لطفاً لینک دعوت کانال را وارد کنید:")
    bot.register_next_step_handler(message, save_channel_info, channel_number, channel_name, username)


def save_channel_info(message, channel_number, channel_name, username):
    invite_link = message.text.strip()
    try:
        add_mandatory_channel(channel_number, channel_name, username, invite_link)
        bot.send_message(message.chat.id, f"✅ کانال {channel_name} با موفقیت اضافه شد.")
    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        bot.send_message(message.chat.id, "❌ خطایی در اضافه کردن کانال رخ داد.")


# حذف کانال با شماره کانال
def process_remove_channel(message):
    try:
        channel_number = message.text.strip()
        remove_channel(channel_number)
        bot.send_message(message.chat.id, f"✅ کانال با شماره {channel_number} حذف شد.")
    except Exception as e:
        logger.error(f"Error removing channel: {e}")
        bot.send_message(message.chat.id, "❌ خطایی در حذف کانال رخ داد.")

#////////////////////////////////////////////////////////////////////////////////////////////////////
@bot.message_handler(commands=["add"])
def add_channel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ فقط ادمین می‌تواند کانال اضافه کند.")
        return

    parts = message.text.split(maxsplit=4)
    if len(parts) != 5:
        bot.reply_to(message, "❌ فرمت دستور اشتباه است. از فرمت زیر استفاده کنید:\n/addchannel <شماره کانال> <نام کانال> <یوزرنیم> <لینک دعوت>")
        return

    channel_number, channel_name, username, invite_link = parts[1:]
    add_mandatory_channel(channel_number, channel_name, username, invite_link)
    bot.reply_to(message, f"✅ کانال {channel_name} اضافه شد.")

@bot.message_handler(commands=["list"])
def list_channels(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ فقط ادمین می‌تواند لیست کانال‌ها را مشاهده کند.")
        return

    channels = get_channels()
    if not channels:
        bot.reply_to(message, "❌ هیچ کانال اجباری‌ای ثبت نشده است.")
        return

    response = "✅ لیست کانال‌های اجباری:\n\n"
    for channel in channels:
        response += f"📌 <b>{channel['channel_name']}</b>\n🔗 یوزرنیم: @{channel['username']}\n📥 لینک: {channel['invite_link']}\n\n"

    bot.reply_to(message, response, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def handle_check_join(call):
    if not handle_missing_channels(call.message.chat.id, call.from_user.id, call.message.message_id):
        bot.edit_message_text("✅ عضویت شما تأیید شد! اکنون می‌توانید از ربات استفاده کنید.", call.message.chat.id, call.message.message_id)

@bot.message_handler(content_types=["document", "photo", "video", "audio", "voice", "sticker", "animation"])
def handle_document(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ فقط ادمین می‌تواند فایل ارسال کند.")
        return

    # استخراج اطلاعات فایل
    content_type = message.content_type
    file = getattr(message, content_type, None)

    # اگر فایل یک لیست باشد (مثلاً برای چندین عکس)، اولین مورد انتخاب می‌شود
    if isinstance(file, list):
        file = file[0]

    file_id = file.file_id if file else None

    if not file_id:
        bot.reply_to(message, "❌ این نوع فایل پشتیبانی نمی‌شود.")
        return

    # تعیین نام فایل
    if content_type == "document":
        file_name = file.file_name or f"file_{uuid.uuid4().hex}"
    elif content_type == "photo":
        file_name = f"photo_{uuid.uuid4().hex}.jpg"
    elif content_type == "video":
        file_name = f"video_{uuid.uuid4().hex}.mp4"
    elif content_type == "audio":
        file_name = f"audio_{uuid.uuid4().hex}.mp3"
    elif content_type == "voice":
        file_name = f"voice_{uuid.uuid4().hex}.ogg"
    elif content_type == "sticker":
        file_name = f"sticker_{uuid.uuid4().hex}.webp"
    elif content_type == "animation":
        file_name = f"animation_{uuid.uuid4().hex}.mp4"
    else:
        file_name = f"unknown_{uuid.uuid4().hex}"

    # ذخیره اطلاعات فایل
    try:
        save_file_metadata(file_name, content_type, file_id)
        bot.reply_to(
            message, f"✅ فایل ذخیره شد. لینک: https://t.me/{bot.get_me().username}?start={add_start_link(file_id)}"
        )
    except ValueError as e:
        bot.reply_to(message, f"⛔ خطا: {str(e)}")
    except sqlite3.IntegrityError:
        # جستجوی لینک ذخیره‌شده قبلی
        cursor.execute("SELECT file_id FROM files WHERE content_type = ? AND file_name = ?", (content_type, file_name))
        result = cursor.fetchone()

        if result:
            previous_file_id = result[0]
            previous_link = f"https://t.me/{bot.get_me().username}?start={add_start_link(previous_file_id)}"
            bot.reply_to(
                message,
                f"⛔ خطای پایگاه داده: این فایل قبلاً ذخیره شده است. لینک: {previous_link}"
            )
        else:
            bot.reply_to(message, "⛔ خطای پایگاه داده: فایل یافت نشد.")

initialize_db()

if __name__ == "__main__":
    logger.info("Bot is running...")
    bot.infinity_polling()
