# import logging
# import os
# import random
# import sqlite3
# import string
# import threading
# import time

# from dotenv import load_dotenv
# from telebot import TeleBot
# from telebot.types import (CallbackQuery, InlineKeyboardButton,
#                            InlineKeyboardMarkup)

# # Load environment variables
# load_dotenv()
# BOT_TOKEN = os.getenv("bot_token")
# if not BOT_TOKEN:
#     raise ValueError("❌ BOT_TOKEN is not set in the .env file.")

# # Admin ID
# ADMIN_ID = 6087657605
# bot_name= 'Uploader Mirali'

# # Channels
# # CHANNELS = [
# #     {"channel_number": "اول", "channel_name": "MiRALi ViBE", "username": "mirali_vibe", "invite_link": "https://t.me/+GrBtMvoIEJxjMGFk"},
# #     {"channel_number": "دوم", "channel_name": "SHADOW R3", "username": "shadow_r3", "invite_link": "https://t.me/+MfS2jBXEQg05MTRk"},
# # ]

# # Logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Bot Initialization
# bot = TeleBot(BOT_TOKEN)

# # Database
# DB_PATH = "telegram_bot.db"

# def get_db_connection():
#     return sqlite3.connect(DB_PATH)

# # افزودن جدول کانال‌ها به دیتابیس
# def initialize_db():
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS start_links (
#             start_link TEXT PRIMARY KEY,
#             file_id TEXT NOT NULL
#         )
#     ''')
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS channels (
#             channel_id INTEGER PRIMARY KEY AUTOINCREMENT,
#             channel_number TEXT NOT NULL,
#             channel_name TEXT NOT NULL,
#             username TEXT NOT NULL,
#             invite_link TEXT NOT NULL
#         )
#     ''')
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS files (
#             file_id TEXT PRIMARY KEY,
#             file_name TEXT NOT NULL,
#             file_format TEXT NOT NULL
#         )
#     ''')
#     conn.commit()
#     conn.close()


# # افزودن کانال به دیتابیس
# def add_channel(channel_number, channel_name, username, invite_link):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('''
#         INSERT INTO channels (channel_number, channel_name, username, invite_link)
#         VALUES (?, ?, ?, ?)
#     ''', (channel_number, channel_name, username, invite_link))
#     conn.commit()
#     conn.close()

# # حذف کانال از دیتابیس
# def remove_channel(channel_id):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('DELETE FROM channels WHERE channel_id = ?', (channel_id,))
#     conn.commit()
#     conn.close()

# # دریافت لیست کانال‌ها از دیتابیس
# def get_channels():
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM channels')
#     channels = cursor.fetchall()
#     conn.close()
#     return [{"channel_number": c[1], "channel_name": c[2], "username": c[3], "invite_link": c[4]} for c in channels]

# # بررسی عضویت کاربر در کانال‌ها
# def get_channels_user_is_not_in(user_id):
#     not_in_channels = []
#     for channel in get_channels():
#         try:
#             status = bot.get_chat_member(f"@{channel['username']}", user_id).status
#             if status in ["left", "kicked"]:
#                 not_in_channels.append(channel)
#         except Exception as e:
#             logger.error(f"Error checking user in channel {channel['username']}: {e}")
#             not_in_channels.append(channel)
#     return not_in_channels

# # Verify if a user is a member of mandatory channels
# def is_user_in_channels(user_id):
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("SELECT username FROM mandatory_channels")
#         channels = cursor.fetchall()
#         conn.close()

#         if not channels:
#             return True  # No mandatory channels to check

#         for channel in channels:
#             username = channel[0]
#             try:
#                 member = bot.get_chat_member(chat_id=f"@{username}", user_id=user_id)
#                 if member.status not in ["member", "administrator", "creator"]:
#                     return False
#             except Exception as e:
#                 logger.error(f"Error checking membership for @{username}: {e}")
#                 return False
#         return True
#     except Exception as e:
#         logger.error(f"Error verifying user membership: {e}")
#         return False

# # Handle start command
# @bot.message_handler(commands=["start"])
# def handle_start(message):
#     try:
#         if len(message.text.split()) < 2:
#             bot.reply_to(message, "❌ لینک نامعتبر است.")
#             return

#         start_link = message.text.split()[1]

#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("SELECT file_id FROM start_links WHERE start_link = ?", (start_link,))
#         result = cursor.fetchone()
#         conn.close()

#         if not result:
#             bot.reply_to(message, "❌ لینک نامعتبر است یا فایل حذف شده است.")
#             return

#         file_id = result[0]

#         # Check if the user is in mandatory channels
#         if not is_user_in_channels(message.from_user.id):
#             bot.reply_to(message, "❌ شما در کانال‌های اجباری عضو نیستید. لطفاً عضو شوید.")
#             return

#         # Send file to user
#         sent_message = bot.send_message(message.chat.id, "✅ فایل در حال ارسال است...")
#         bot.send_document(message.chat.id, file_id)

#         # Delete the "sending file" message
#         bot.delete_message(chat_id=message.chat.id, message_id=sent_message.message_id)

#     except Exception as e:
#         logger.error(f"Error in /start handler: {e}")
#         bot.reply_to(message, "❌ خطایی رخ داد.")

# # Add mandatory channels to the database
# def add_mandatory_channel(channel_number, channel_name, username, invite_link):
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute(
#             "INSERT INTO mandatory_channels (channel_number, channel_name, username, invite_link) VALUES (?, ?, ?, ?)",
#             (channel_number, channel_name, username, invite_link)
#         )
#         conn.commit()
#         conn.close()
#         return True
#     except Exception as e:
#         logger.error(f"Error adding mandatory channel: {e}")
#         return False

# # Command to add a mandatory channel
# @bot.message_handler(commands=["addchannel"])
# def add_channel(message):
#     try:
#         if message.from_user.id != ADMIN_ID:
#             bot.reply_to(message, "❌ فقط ادمین می‌تواند کانال اضافه کند.")
#             return

#         # Expected format: /addchannel <channel_number> <channel_name> <username> <invite_link>
#         parts = message.text.split(maxsplit=4)
#         if len(parts) != 5:
#             bot.reply_to(
#                 message,
#                 "❌ فرمت دستور اشتباه است. از فرمت زیر استفاده کنید:\n"
#                 "/addchannel <شماره کانال> <نام کانال> <یوزرنیم> <لینک دعوت>"
#             )
#             return

#         channel_number, channel_name, username, invite_link = parts[1:]

#         success = add_mandatory_channel(channel_number, channel_name, username, invite_link)
#         if success:
#             bot.reply_to(message, f"✅ کانال {channel_name} اضافه شد.")
#         else:
#             bot.reply_to(message, "❌ خطایی در اضافه کردن کانال رخ داد.")
#     except Exception as e:
#         logger.error(f"Error adding channel: {e}")
#         bot.reply_to(message, "❌ خطایی رخ داد.")

# # Command to remove a mandatory channel
# @bot.message_handler(commands=["removechannel"])
# def remove_channel(message):
#     try:
#         if message.from_user.id != ADMIN_ID:
#             bot.reply_to(message, "❌ فقط ادمین می‌تواند کانال حذف کند.")
#             return

#         # Expected format: /removechannel <username>
#         parts = message.text.split(maxsplit=1)
#         if len(parts) != 2:
#             bot.reply_to(message, "❌ فرمت دستور اشتباه است. از فرمت زیر استفاده کنید:\n/removechannel <یوزرنیم>")
#             return

#         username = parts[1]

#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("DELETE FROM mandatory_channels WHERE username = ?", (username,))
#         conn.commit()
#         conn.close()

#         if cursor.rowcount > 0:
#             bot.reply_to(message, f"✅ کانال با یوزرنیم @{username} حذف شد.")
#         else:
#             bot.reply_to(message, "❌ کانالی با این یوزرنیم یافت نشد.")
#     except Exception as e:
#         logger.error(f"Error removing channel: {e}")
#         bot.reply_to(message, "❌ خطایی رخ داد.")

# # Command to list all mandatory channels
# @bot.message_handler(commands=["list"])
# def list_channels(message):
#     try:
#         if message.from_user.id != ADMIN_ID:
#             bot.reply_to(message, "❌ فقط ادمین می‌تواند لیست کانال‌ها را مشاهده کند.")
#             return

#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("SELECT channel_name, username, invite_link FROM mandatory_channels")
#         channels = cursor.fetchall()
#         conn.close()

#         if not channels:
#             bot.reply_to(message, "❌ هیچ کانال اجباری‌ای ثبت نشده است.")
#             return

#         response = "✅ لیست کانال‌های اجباری:\n\n"
#         for channel in channels:
#             response += f"📌 <b>{channel[0]}</b>\n"
#             response += f"🔗 یوزرنیم: @{channel[1]}\n"
#             response += f"📥 لینک: {channel[2]}\n\n"

#         bot.reply_to(message, response, parse_mode="HTML")
#     except Exception as e:
#         logger.error(f"Error listing channels: {e}")
#         bot.reply_to(message, "❌ خطایی رخ داد.")

# # Check user subscription
# def get_channels_user_is_not_in(user_id):
#     not_in_channels = []
#     for channel in CHANNELS:
#         try:
#             status = bot.get_chat_member(f"@{channel['username']}", user_id).status
#             if status in ["left", "kicked"]:
#                 not_in_channels.append(channel)
#         except Exception as e:
#             logger.error(f"Error checking user in channel {channel['username']}: {e}")
#             not_in_channels.append(channel)
#     return not_in_channels

# # Send join prompt
# def send_join_prompt(chat_id, missing_channels, message_id=None):
#     markup = InlineKeyboardMarkup()
#     for channel in missing_channels:
#         markup.add(InlineKeyboardButton(f"عضویت در کانال {channel['channel_number']}", url=channel["invite_link"]))
#     markup.add(InlineKeyboardButton("عضو شدم ✅", callback_data="check_join"))
#     message_text = "❌ برای استفاده از ربات، ابتدا باید در کانال‌های زیر عضو شوید:"
#     if message_id:
#         bot.edit_message_text(message_text, chat_id, message_id, reply_markup=markup)
#     else:
#         bot.send_message(chat_id, message_text, reply_markup=markup)

# # Handle missing channels
# def handle_missing_channels(chat_id, user_id, message_id=None):
#     missing_channels = get_channels_user_is_not_in(user_id)
#     if missing_channels:
#         send_join_prompt(chat_id, missing_channels, message_id)
#         return True
#     return False

# # Generate start link
# def generate_start_link():
#     return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# # Add start link
# def add_start_link(file_id):
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("SELECT start_link FROM start_links WHERE file_id = ?", (file_id,))
#         result = cursor.fetchone()
#         if result:
#             conn.close()
#             return result[0]

#         start_link = generate_start_link()
#         cursor.execute("INSERT INTO start_links (start_link, file_id) VALUES (?, ?)", (start_link, file_id))
#         conn.commit()
#         conn.close()
#         return start_link
#     except Exception as e:
#         logger.error(f"Error adding start link: {e}")
#         raise

# # Save file metadata to database
# def save_file_metadata(file_name, file_format, file_id):
#     try:
#         if not file_name:  # If the file doesn't have a name, use a default name
#             file_name = "untitled_file"

#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute(
#             "INSERT INTO files (file_name, file_format, file_id) VALUES (?, ?, ?)",
#             (file_name, file_format, file_id)
#         )
#         conn.commit()
#         conn.close()
#     except Exception as e:
#         logger.error(f"Error saving file metadata: {e}")
#         raise


# # Handle document upload
# @bot.message_handler(content_types=["photo", "video", "document", "audio", "voice", "sticker", "animation"])
# def handle_document(message):
#     try:
#         if message.from_user.id != ADMIN_ID:
#             bot.reply_to(message, "❌ فقط ادمین می‌تواند فایل ارسال کند.")
#             return

#         file_id = None
#         file_name = None
#         file_format = None

#         # Determine file type and name
#         if message.content_type == "photo":
#             file_id = message.photo[-1].file_id
#             file_name = "عکس"
#             file_format = "photo"
#         elif message.content_type == "video":
#             file = message.video
#             file_id = file.file_id
#             file_name = file.file_name if hasattr(file, "file_name") else "video_without_name"
#             file_format = "video"
#         elif message.content_type == "document":
#             file = message.document
#             file_id = file.file_id
#             file_name = file.file_name if hasattr(file, "file_name") else "document_without_name"
#             file_format = "document"
#         elif message.content_type == "audio":
#             file = message.audio
#             file_id = file.file_id
#             file_name = file.file_name if hasattr(file, "file_name") else "audio_without_name"
#             file_format = "audio"
#         elif message.content_type == "voice":
#             file = message.voice
#             file_id = file.file_id
#             file_name = "voice_note"
#             file_format = "voice"
#         elif message.content_type == "sticker":
#             file = message.sticker
#             file_id = file.file_id
#             file_name = "sticker"
#             file_format = "sticker"
#         elif message.content_type == "animation":
#             file = message.animation
#             file_id = file.file_id
#             file_name = "animation"
#             file_format = "animation"

#         # Check if file_id is valid
#         if not file_id:
#             bot.reply_to(message, "❌ این نوع فایل پشتیبانی نمی‌شود.")
#             return

#         # Generate a start link for the file
#         start_link = add_start_link(file_id)
#         start_url = f"https://t.me/{bot.get_me().username}?start={start_link}"

#         # Save the file metadata to the database
#         save_file_metadata(file_name, file_format, file_id)

#         bot.reply_to(
#             message,
#             f"✅ فایل شما ذخیره شد. برای دسترسی به فایل، از لینک زیر استفاده کنید:\n\n"
#             f"{start_url}",
#             reply_markup=None,
#             parse_mode="HTML",
#         )
#     except Exception as e:
#         logger.error(f"Error handling document: {e}")
#         bot.send_message(message.chat.id, "❌ خطایی رخ داد.")

# # Handle start command
# @bot.message_handler(commands=["start"])
# def handle_start_link(message):
#     try:
#         if handle_missing_channels(message.chat.id, message.from_user.id):
#             return

#         parts = message.text.split(" ")
#         if len(parts) < 2 or not parts[1].isalnum():
#             bot.reply_to(message, f"به ربات {bot_name} خوش اومدید!")
#             return

#         start_link = parts[1]
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("SELECT file_id FROM start_links WHERE start_link = ?", (start_link,))
#         result = cursor.fetchone()
#         conn.close()

#         if not result:
#             bot.reply_to(message, f"به ربات {bot_name} خوش اومداست!")
#             return

#         file_id = result[0]
#         bot.send_document(
#             message.chat.id,
#             file_id,
#             caption="این فایل توسط ربات ساخته شده است: @mirali_official"
#         )
#     except Exception as e:
#         logger.error(f"Error handling start command: {e}")
#         bot.reply_to(message, "❌ خطایی رخ داد.")


# def delete_message_after_delay(chat_id, *message_ids):
#     time.sleep(60)  # Wait for 1 minute
#     for message_id in message_ids:
#         try:
#             bot.delete_message(chat_id, message_id)
#         except Exception as e:
#             logger.error(f"Error deleting message {message_id}: {e}")



# # Handle help command
# @bot.message_handler(commands=["help"])
# def handle_help(message):
#     help_text = (
#         "🤖 راهنمای استفاده از ربات:\n\n"
#         "1️⃣ برای دریافت فایل‌ها باید ابتدا در کانال‌های مشخص شده عضو شوید.\n"
#         "2️⃣ پس از عضویت، از دکمه 'عضو شدم ✅' استفاده کنید تا عضویت شما تأیید شود.\n"
#         "3️⃣ فایل‌ها را می‌توانید از طریق لینک استارت اختصاصی دریافت کنید.\n"
#         "4️⃣ تنها ادمین می‌تواند فایل‌ها را به ربات ارسال کند."
#     )
#     bot.reply_to(message, help_text)

# @bot.message_handler(commands=['giveme11228'])
# def sendata(message):
#     database = '/home/miraliofficial/telegram_bot.db'
#     if message.from_user.id != ADMIN_ID:
#         bot.reply_to(message, "❌ فقط ادمین می‌تواند فایل ارسال کند.")
#         return
#     if os.path.exists(database):
#         with open(database, 'rb') as db_file:
#             bot.send_document(message.chat.id, db_file)
#     else:
#         bot.reply_to(message, "❌ فایل پایگاه داده پیدا نشد.")

# # Handle join confirmation callback
# @bot.callback_query_handler(func=lambda call: call.data == "check_join")
# def handle_check_join(call: CallbackQuery):
#     try:
#         if not handle_missing_channels(call.message.chat.id, call.from_user.id, call.message.message_id):
#             bot.edit_message_text('''✅ عضویت شما تأیید شد!
#             اکنون می‌توانید از ربات استفاده کنید.''',
#             call.message.chat.id, call.message.message_id)
#     except Exception as e:
#         logger.error(f"Error in handle_check_join: {e}")
#         bot.send_message(call.message.chat.id,
#         '''برای ربات مشکلی پیش اومده ، لطفا با دستور /help
#         مشکل رو به پشتیبانی اطلاع بدهید 🌹 .''')

# # Initialize database
# initialize_db()

# # Polling
# if __name__ == "__main__":
#     logger.info("Bot is running...")
#     bot.infinity_polling()

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////
