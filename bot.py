import os
from telethon import TelegramClient, events, Button
from dotenv import load_dotenv
import logging
from telethon.tl.custom import Button
from telethon.errors import RPCError
import json
import ti

load_dotenv()
TOKEN = os.getenv('token')
API_ID = os.getenv('api_id')
API_HASH = os.getenv('api_hash')
ADMIN_ID = int(os.getenv('admin_id')) 

if not TOKEN or not API_ID or not API_HASH or not ADMIN_ID:
    raise ValueError("اطلاعات توکن، API_ID، API_HASH یا ADMIN_ID ناقص است. لطفاً فایل .env را بررسی کنید.")

# تنظیمات لاگ‌ها
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ایجاد کلاینت تلگرام
bot = TelegramClient('bot', API_ID, API_HASH)

# متغیر برای ذخیره اطلاعات کاربران
user_data = {}

# سؤالات
questions = [
    "1️⃣ نام رباتی که می‌خواهید چیست؟",
    "2️⃣ موضوع فعالیت ربات را مشخص کنید.",
    "3️⃣ آیا ربات شما نیاز به اتصال به API خاصی دارد؟ اگر بله، توضیح دهید.",
    "4️⃣ آیا ربات شما نیاز به مدیریت چندین کاربر دارد؟",
    "5️⃣ آیا ربات شما نیاز به سیستم پرداخت دارد؟",
    "6️⃣ توضیحات اضافی در مورد ویژگی‌های ربات شما.",
    "7️⃣ آیدی تلگرام شما برای ارتباط‌های بعدی چیست؟"
]

# دکمه‌های صفحه شروع
start_markup = [
    [Button.inline('سفارش ربات', b'Order')]
]

# دکمه‌های صفحه سفارش
order_markup = [
    [Button.inline('بازگشت ↩️', b'back_to_start')]
]

# مدیریت دستور /start
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

def save_data():
    with open('orders.json', 'w', encoding='utf-8') as file:
        json.dump(orders, file, ensure_ascii=False, indent=4)

orders = {}

def load_data():
    global orders
    try:
        with open('orders.json', 'r', encoding='utf-8') as file:
            loaded_orders = json.load(file)  # Don't overwrite directly
            # Update existing orders and add new ones
            for user_id, order_data in loaded_orders.items():
                orders[int(user_id)] = {  # Ensure user_id is an integer
                    "answers": order_data.get("answers", []),
                    "status": order_data.get("status", "pending"),
                    "price": order_data.get("price", None)
                }
    except FileNotFoundError:
        pass # It's okay if the file doesn't exist initially

load_data()

# مدیریت دکمه "سفارش ربات"
@bot.on(events.CallbackQuery(data=b'Order'))
async def start_questions(event):
    user_id = event.sender_id

    # مقداردهی اولیه اطلاعات کاربر
    user_data[user_id] = {"answers": [], "current_question": 0}

    # ارسال اولین سؤال
    await event.edit(
        text=questions[0],
        buttons=[Button.inline("لغو", b'cancel')]
    )

# مدیریت پاسخ‌های کاربران
@bot.on(events.NewMessage)
async def handle_answers(event):
    user_id = event.sender_id
    
    # بررسی اینکه آیا کاربر در فرآیند پاسخ‌دهی است
    if user_id in user_data and "current_question" in user_data[user_id]:
        current_question = user_data[user_id]["current_question"]

        # ذخیره پاسخ کاربر
        user_data[user_id]["answers"].append(event.text)

        # بررسی اینکه آیا هنوز سؤالات بیشتری وجود دارد
        if current_question + 1 < len(questions):
            user_data[user_id]["current_question"] += 1
            next_question = questions[current_question + 1]

            # ارسال سؤال بعدی
            await event.respond(next_question, buttons=[Button.inline("لغو", b'cancel')])
        else:
            # اتمام پرسش‌ها
            answers = user_data[user_id]["answers"]
            summary = "\n".join([f"{i+1}. {questions[i]}: {answers[i]}" for i in range(len(answers))])

            await event.respond(
                f"✅ پاسخ‌های شما ثبت شد:\n\n{summary}\n\nآیا این اطلاعات تایید می‌شود؟",
                buttons=[
                    Button.inline("تایید", b'confirm'),
                    Button.inline("لغو", b'cancel')
                ]
            )
            # پاک کردن وضعیت پرسش
            del user_data[user_id]["current_question"]

# مدیریت دکمه "لغو"
@bot.on(events.CallbackQuery(data=b'cancel'))
async def cancel_order(event):
    user_id = event.sender_id
    if user_id in user_data:
        del user_data[user_id]
    await event.edit("❌ فرآیند ثبت سفارش لغو شد.")

# ذخیره اطلاعات سفارش‌ها
orders = {}  # key: user_id, value: {"answers": [...], "status": "pending"}

# مدیریت دکمه "تایید"
@bot.on(events.CallbackQuery(data=b'confirm'))
async def confirm_order(event):
    user_id = event.sender_id
    if user_id in user_data:
        answers = user_data[user_id]["answers"]

        # ارسال اطلاعات به ادمین
        summary = "\n".join([f"{i+1}. {questions[i]}: {answers[i]}" for i in range(len(answers))])
        try:
            await bot.send_message(ADMIN_ID, f"📩 سفارش جدید:\n\n{summary}\n\nاز طرف: {user_id}",
                                   buttons=[
                                       Button.inline("تایید", f"approve_{user_id}".encode()),
                                       Button.inline("رد", f"reject_{user_id}".encode())
                                   ])
            await event.edit("✅ سفارش شما با موفقیت ثبت شد و برای بررسی به ادمین ارسال گردید.")
        except Exception as e:
            await event.edit("⚠️ خطا در ارسال سفارش به ادمین.")
            logger.error(f"خطا در ارسال سفارش: {e}")

        del user_data[user_id] 

# مدیریت تایید یا رد سفارش توسط ادمین
@bot.on(events.CallbackQuery(pattern=b'approve_\d+'))
async def admin_approve_order(event):
    user_id = int(event.data.decode().split('_')[1])
    if user_id in orders:
        orders[user_id]["status"] = "approved"
        save_data()
        await bot.send_message(user_id, "✅ سفارش شما توسط ادمین تایید شد.")
        await event.edit("سفارش تایید شد.")

@bot.on(events.CallbackQuery(pattern=b'reject_\d+'))
async def admin_reject_order(event):
    user_id = int(event.data.decode().split('_')[1])
    if user_id in orders:
        orders[user_id]["status"] = "rejected"
        save_data()
        await bot.send_message(user_id, "❌ سفارش شما توسط ادمین رد شد.")
        await event.edit("سفارش رد شد.")

# مدیریت تایید سفارش و ارسال قیمت توسط ادمین
@bot.on(events.CallbackQuery(pattern=r'approve_(\d+)'))
async def approve_order(event):
    user_id = int(event.data.decode().split('_')[1])
    if user_id in orders and orders[user_id]["status"] == "pending":
        await event.respond(f"💰 لطفاً قیمت سفارش را وارد کنید:", buttons=[Button.inline("لغو", b'cancel')])

        # ذخیره وضعیت سفارش برای ورود قیمت
        orders[user_id]["status"] = "awaiting_price"

@bot.on(events.NewMessage)
async def handle_price(event):
    if event.reply_to_msg_id:
        reply_msg = await event.get_reply_message()
        user_id = reply_msg.sender_id

        if user_id in orders and orders[user_id]["status"] == "pending":
            try:
                price = int(event.text)  # قیمت وارد شده را به عدد تبدیل کنید
                orders[user_id]["status"] = "price_sent"
                orders[user_id]["price"] = price
                save_data()

                # ارسال قیمت به کاربر
                await bot.send_message(
                    user_id,
                    f"💰 قیمت سفارش شما: {price} تومان\n\nآیا مایل به ادامه هستید؟",
                    buttons=[
                        Button.inline("ادامه", f"accept_{user_id}".encode()),
                        Button.inline("لغو", b'cancel')
                    ]
                )
                await event.respond("✅ قیمت برای کاربر ارسال شد.")
            except ValueError:
                await event.respond("❌ لطفاً قیمت را به صورت عددی وارد کنید.")
        else:
            await event.respond("❌ وضعیت سفارش برای تعیین قیمت مناسب نیست.")
    else:
        await event.respond("❌ لطفاً پیام کاربر را ریپلای کنید.")

# مدیریت ادامه سفارش توسط کاربر
@bot.on(events.CallbackQuery(pattern=r'accept_(\d+)'))
async def accept_price(event):
    user_id = int(event.data.decode().split('_')[1])
    if user_id in orders and orders[user_id]["status"] == "price_sent":
        await event.edit("✅ لطفاً شرایط و ضوابط را مطالعه کرده و عکس احراز هویت خود را ارسال کنید.")
        orders[user_id]["status"] = "awaiting_verification"
        
# مدیریت دریافت عکس احراز هویت از کاربر
@bot.on(events.NewMessage)
async def handle_verification_photo(event):
    user_id = event.sender_id

    # بررسی اینکه کاربر در مرحله ارسال عکس است
    if user_id in orders and orders[user_id]["status"] == "awaiting_verification":
        if event.photo:  # بررسی اینکه پیام شامل عکس است
            photo = event.photo

            # ارسال عکس به ادمین برای تایید
            admin_id = ADMIN_ID 
            await bot.send_message(
                admin_id,
                f"📸 عکس احراز هویت برای سفارش کاربر {user_id} ارسال شد.\n\nآیا این عکس تایید می‌شود؟",
                file=photo,
                buttons=[
                    Button.inline("تایید", f"verify_{user_id}".encode()),
                    Button.inline("رد", f"reject_photo_{user_id}".encode())
                ]
            )

            await event.respond("✅ عکس شما برای بررسی به ادمین ارسال شد. لطفاً منتظر بمانید.")
            orders[user_id]["status"] = "photo_sent"
        else:
            await event.respond("❌ لطفاً یک عکس معتبر ارسال کنید.")

# مدیریت تایید عکس توسط ادمین
@bot.on(events.CallbackQuery(pattern=r'verify_(\d+)'))
async def verify_photo(event):
    user_id = int(event.data.decode().split('_')[1])
    if user_id in orders and orders[user_id]["status"] == "photo_sent":
        orders[user_id]["status"] = "verified"
        save_data()

        await bot.send_message(user_id, "✅ عکس شما تایید شد. لطفاً به مرحله پرداخت بروید.")
        await event.respond("✅ عکس تایید شد و به کاربر اطلاع داده شد.")

@bot.on(events.CallbackQuery(pattern=r'reject_photo_(\d+)'))
async def reject_photo(event):
    user_id = int(event.data.decode().split('_')[1])
    if user_id in orders and orders[user_id]["status"] == "photo_sent":
        orders[user_id]["status"] = "awaiting_verification"
        save_data()

        await bot.send_message(user_id, "❌ عکس شما رد شد. لطفاً دوباره تلاش کنید.")
        await event.respond("❌ عکس رد شد و به کاربر اطلاع داده شد.")

# نمایش اطلاعات پرداخت به کاربر
@bot.on(events.CallbackQuery(data=b'proceed_to_payment'))
async def proceed_to_payment(event):
    user_id = event.sender_id
    if user_id in orders and orders[user_id]["status"] == "verified":
        payment_info = """
💳 اطلاعات پرداخت:

🔹 شماره کارت: 1234-5678-9012-3456
🔹 نام صاحب حساب: میرعلی شاپ
🔹 مبلغ: {} تومان

لطفاً پس از پرداخت، تصویر رسید را ارسال کنید.
        """.format(orders[user_id]["price"])

        await event.edit(payment_info, buttons=[Button.inline("لغو", b'cancel')])
        orders[user_id]["status"] = "awaiting_payment"
    else:
        await event.respond("❌ شما در مرحله صحیح برای پرداخت نیستید.")

# دریافت رسید پرداخت از کاربر
@bot.on(events.NewMessage(func=lambda e: e.sender_id in user_data and "awaiting_payment" in user_data[e.sender_id]))
async def handle_payment_receipt(event):
    user_id = event.sender_id
    del user_data[user_id]["awaiting_payment"] # حذف state پس از دریافت رسید
    if event.photo:  # بررسی اینکه پیام شامل عکس است
            photo = event.photo

            # ارسال رسید به ادمین برای تایید
            admin_id = ADMIN_ID 
            await bot.send_message(
                admin_id,
                f"📩 رسید پرداخت از کاربر {user_id} دریافت شد.\n\nآیا این رسید تایید می‌شود؟",
                file=photo,
                buttons=[
                    Button.inline("تایید", f"approve_payment_{user_id}".encode()),
                    Button.inline("رد", f"reject_payment_{user_id}".encode())
                ]
            )

            await event.respond("✅ رسید شما برای بررسی به ادمین ارسال شد. لطفاً منتظر تایید باشید.")
            orders[user_id]["status"] = "receipt_sent"
    else:
            await event.respond("❌ لطفاً یک تصویر معتبر از رسید ارسال کنید.")

# تایید رسید توسط ادمین
@bot.on(events.CallbackQuery(pattern=r'approve_(\d+)'))
async def approve_order(event):
    user_id = int(event.data.decode().split('_')[1])
    if user_id in orders and orders[user_id]["status"] == "pending":
        await bot.send_message(
            ADMIN_ID,
            f"لطفاً قیمت سفارش کاربر {user_id} را وارد کنید:"
        )
        orders[user_id]["status"] = "awaiting_price"
        save_data()

        # اطلاع به ادمین
        await event.respond("✅ رسید تایید شد و به کاربر اطلاع داده شد.")

# رد رسید توسط ادمین
@bot.on(events.CallbackQuery(pattern=r'reject_payment_(\d+)'))
async def reject_payment(event):
    user_id = int(event.data.decode().split('_')[1])
    if user_id in orders and orders[user_id]["status"] == "receipt_sent":
        await bot.send_message(user_id, "❌ رسید شما رد شد. لطفاً دوباره تلاش کنید.")
        orders[user_id]["status"] = "awaiting_payment"

        # اطلاع به ادمین
        await event.respond("❌ رسید رد شد و به کاربر اطلاع داده شد.")
        
# ارسال فایل سورس کد توسط ادمین
@bot.on(events.NewMessage(from_users=ADMIN_ID)) 
async def send_source_file(event):
    if event.reply_to_msg_id:
        # بررسی اینکه پیام ادمین به پیام کاربر ریپلای شده است
        reply_msg = await event.get_reply_message()
        user_id = reply_msg.sender_id

        if user_id in orders and orders[user_id]["status"] == "payment_approved":
            if event.file:  # بررسی اینکه فایل ارسال شده است
                file = event.file

                # ارسال فایل به کاربر
                await bot.send_message(
                    user_id,
                    "✅ سورس کد ربات شما آماده است! فایل زیر را دانلود کنید:",
                    file=file
                )

                # درخواست بازخورد از کاربر
                await bot.send_message(
                    user_id,
                    "💬 لطفاً میزان رضایت خود از خدمات ما را ثبت کنید:\n\n"
                    "🔹 عالی\n🔹 خوب\n🔹 متوسط\n🔹 ضعیف",
                    buttons=[
                        [Button.inline("عالی", b'feedback_great')],
                        [Button.inline("خوب", b'feedback_good')],
                        [Button.inline("متوسط", b'feedback_average')],
                        [Button.inline("ضعیف", b'feedback_poor')]
                    ]
                )

                await event.respond("✅ فایل سورس کد به کاربر ارسال شد.")
                orders[user_id]["status"] = "source_sent"
            else:
                await event.respond("❌ لطفاً یک فایل معتبر ارسال کنید.")
        else:
            await event.respond("❌ این کاربر هنوز پرداخت خود را تایید نکرده است.")
    else:
        await event.respond("❌ لطفاً پیام کاربر را ریپلای کنید.")

# دریافت بازخورد از کاربر
@bot.on(events.CallbackQuery(pattern=r'feedback_(\w+)'))
async def handle_feedback(event):
    user_id = event.sender_id
    feedback = event.data.decode().split('_')[1]

    feedback_texts = {
        "great": "عالی",
        "good": "خوب",
        "average": "متوسط",
        "poor": "ضعیف"
    }

    if feedback in feedback_texts:
        await event.respond(f"✅ از بازخورد شما متشکریم: {feedback_texts[feedback]}")

        # ارسال بازخورد به ادمین
        admin_id = ADMIN_ID 
        await bot.send_message(
            admin_id,
            f"📩 بازخورد جدید از کاربر {user_id}:\n\n{feedback_texts[feedback]}"
        )

        # به‌روزرسانی وضعیت سفارش
        if user_id in orders:
            orders[user_id]["status"] = "feedback_received"
    else:
        await event.respond("❌ بازخورد نامعتبر است.")

# مدیریت خطاهای عمومی
@bot.on(events.NewMessage)
async def handle_general_errors(event):
    try:
        # در اینجا، مدیریت پیام‌ها یا عملیات خاصی که مد نظر دارید را قرار دهید.
        pass
    except RPCError as e:
        logger.error(f"خطای تلگرام: {str(e)}")
        await event.respond("❌ خطای تلگرام رخ داده است. لطفاً دوباره تلاش کنید.")
    except ValueError as e:
        logger.error(f"خطای مقدار نامعتبر: {str(e)}")
        await event.respond("❌ مقدار وارد شده نامعتبر است.")
    except Exception as e:
        logger.error(f"خطای غیرمنتظره: {str(e)}")
        await event.respond("❌ خطای غیرمنتظره‌ای رخ داده است.")


# به‌روزرسانی وضعیت سفارش و ذخیره اطلاعات
def update_order_status(user_id, status):
    if user_id in orders:
        orders[user_id]["status"] = status
        save_data()

# پیام‌های کاربرپسند
async def send_user_message(user_id, message, buttons=None):
    try:
        await bot.send_message(user_id, message, buttons=buttons)
    except RPCError as e:
        logger.error(f"خطا در ارسال پیام به کاربر {user_id}: {str(e)}")



# اجرای ربات
if __name__ == '__main__':
    bot.start(bot_token=TOKEN)
    bot.run_until_disconnected()
