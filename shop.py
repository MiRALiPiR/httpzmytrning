import os
from telethon import TelegramClient, events, Button
from dotenv import load_dotenv
import logging

# بارگذاری تنظیمات از فایل .env
load_dotenv()
TOKEN = os.getenv('token')
API_ID = int(os.getenv('api_id'))  # تبدیل به عدد
API_HASH = os.getenv('api_hash')

# بررسی مقادیر ضروری
if not TOKEN or not API_ID or not API_HASH:
    raise ValueError("اطلاعات توکن، API_ID یا API_HASH ناقص است. لطفاً فایل .env را بررسی کنید.")

# تنظیمات لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ایجاد کلاینت Telethon
bot = TelegramClient('bot', API_ID, API_HASH)

# دکمه‌ها
start_markup = [
    [Button.inline('سفارش ربات', b'Order')]
]

order_markup = [
    [Button.inline('بازگشت ↩️', b'back_to_start')]
]

# مدیریت دستور /start
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    try:
        await event.reply(
            '''درود بر شما 🌹
به ربات ثبت سفارشات میرعلی شاپ خوش اومدید 💎

🔰 آیدی کانال: @MiRALi_Shop_OG  
🆔 آیدی مالک مجموعه: @MiRALi_OFFiCiAL  

<strong>▼برای ثبت سفارش روی دکمه زیر کلیک کنید▼</strong>''',
            parse_mode='html',
            buttons=start_markup
        )
    except Exception as e:
        logger.error(f"خطا در مدیریت دستور /start: {str(e)}")

# مدیریت دکمه سفارش ربات
@bot.on(events.CallbackQuery(data=b'Order'))
async def order(event):
    try:
        await event.edit(
            text='''💎 به بخش سفارش ربات خوش اومدین 🌹
🟢 در این بخش شما باید اطلاعات رباتی 
رو که قصد ساختنش رو دارید وارد کنید ❗️
🔴 بعد از ثبت درخواست شما 
سفارشتون توی لیست چک و بررسی 
قراره میگیره تا که براتون محاسبه قیمت کنه ✅''',
            parse_mode='html',
            buttons=order_markup
        )
    except Exception as e:
        logger.error(f"خطا در مدیریت دکمه سفارش: {str(e)}")

# مدیریت دکمه بازگشت
@bot.on(events.CallbackQuery(data=b'back_to_start'))
async def back_to_start(event):
    try:
        await event.edit(
            text='''درود بر شما 🌹
به ربات ثبت سفارشات میرعلی شاپ خوش اومدید 💎

🔰 آیدی کانال: @MiRALi_Shop_OG  
🆔 آیدی مالک مجموعه: @MiRALi_OFFiCiAL  

<strong>▼برای ثبت سفارش روی دکمه زیر کلیک کنید▼</strong>''',
            parse_mode='html',
            buttons=start_markup
        )
    except Exception as e:
        logger.error(f"خطا در مدیریت دکمه بازگشت: {str(e)}")

# اجرای ربات
async def main():
    try:
        await bot.start(bot_token=TOKEN)
        me = await bot.get_me()
        logger.info(f"ربات با موفقیت متصل شد! یوزرنیم: @{me.username}")
        logger.info("ربات آماده است.")
        await bot.run_until_disconnected()
    except Exception as e:
        logger.error(f"خطا در اجرای ربات: {str(e)}")

if __name__ == '__main__':
    bot.loop.run_until_complete(main())
