import os
from telethon import TelegramClient, events, Button
from dotenv import load_dotenv
import logging

# بارگذاری اطلاعات از فایل .env
load_dotenv()
TOKEN = os.getenv('bot_token')
API_ID = os.getenv('api_id')
API_HASH = os.getenv('api_hash')

if not TOKEN or not API_ID or not API_HASH:
    raise ValueError("اطلاعات توکن، API_ID یا API_HASH ناقص است. لطفاً فایل .env را بررسی کنید.")

# تنظیمات لاگ‌ها
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ایجاد کلاینت تلگرام
bot = TelegramClient('bot', API_ID, API_HASH)

async def main():
    try:
        # اتصال به تلگرام با توکن
        await bot.start(bot_token=TOKEN)

        # گرفتن اطلاعات ربات
        me = await bot.get_me()
        logger.info(f"ربات با موفقیت متصل شد! یوزرنیم ربات: @{me.username}")
        print(f"ربات آماده است: @{me.username}")

    except Exception as e:
        logger.error(f"خطا در اتصال: {str(e)}")

start_markup = [
    [Button.inline('سفارش ربات', b'Order')]
]

order_markup = [
    [Button.inline('بازگشت ↩️', b'back_to_start')]
]

@bot.on(events.NewMessage(pattern=r'/start'))
async def start(event):
    await event.reply(
        '''درود بر شما 🌹
به ربات ثبت سفارشات میرعلی شاپ خوش اومدید 💎

🔰 آیدی کانال: @MiRALi_Shop_OG  
🆔 آیدی مالک مجموعه: @MiRALi_OFFiCiAL  

<strong>▼برای ثبت سفارش روی دکمه زیر کلیک کنید▼</strong>''',
        parse_mode='html',
        buttons=start_markup
    )

@bot.on(events.CallbackQuery(data=b'Order'))
async def order(event):
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

# اجرای ربات
if __name__ == '__main__':
    bot.loop.run_until_complete(main())
