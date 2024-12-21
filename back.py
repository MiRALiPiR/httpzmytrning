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
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////   

order_button = telebot.types.InlineKeyboardButton('سفارش ربات', callback_data='Order')
markup = telebot.types.InlineKeyboardMarkup(row_width=2)
markup.add(order_button)

# مدیریت callback برای سفارش ربات
@bot.callback_query_handler(func=lambda call: call.data == 'Order')
def order(call):
    # دکمه بازگشت
    back_button = telebot.types.InlineKeyboardButton('بازگشت ↩️', callback_data='back_to_start')
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(back_button)

    # ویرایش پیام با دکمه بازگشت
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='''💎 به بخش سفارش ربات خوش اومدین 🌹
🟢 در این بخش شما باید اطلاعات رباتی 
رو که قصد ساختنش رو دارید وارد کنید ❗️
🔴 بعد از ثبت درخواست شما 
سفارشتون توی لیست چک و بررسی 
قراره میگیره تا که براتون محاسبه قیمت کنه ✅''',
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_start')
def back_to_start(call):
    # حذف پیام قبلی
    bot.delete_message(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id
    )
    
    # ارسال پیام جدید
    bot.send_message(
        chat_id=call.message.chat.id,
        text='''درود بر شما 🌹
به ربات ثبت سفارشات میرعلی شاپ خوش اومدید 💎

<blockquote>🔰 آیدی کانال: @MiRALi_Shop_OG </blockquote>
<blockquote>🆔 آیدی مالک مجموعه: @MiRALi_OFFiCiAL </blockquote>

<strong>▼برای ثبت سفارش روی دکمه زیر کلیک کنید▼</strong>''',
        parse_mode='HTML',
        reply_markup=markup
    )

# مدیریت دستور /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        '''درود بر شما 🌹
به ربات ثبت سفارشات میرعلی شاپ خوش اومدید 💎

<blockquote>🔰 کانال : @MiRALi_Shop_OG </blockquote>
<blockquote>🆔کانال اعتماد : @TrusT_MiRALi </blockquote>

<strong>▼توجه: برای ثبت سفارش روی دکمه زیر کلیک کنید ▼</strong>''',
        parse_mode='HTML',
        reply_markup=markup
    )

#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f'Error on polling: {str(e)}')

bot.polling()