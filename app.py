from telethon import TelegramClient, events, Button
import os
import json
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv('api_id')
API_HASH = os.getenv('api_hash')
BOT_TOKEN = os.getenv('token')
ADMIN_ID = int(os.getenv('admin_id'))

client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Path to the JSON database file
DB_PATH = "messages_db.json"
user_data = {}

# Load or initialize the JSON database
def load_database():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}}

def save_database(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

messages_db = load_database()

# List of questions
questions = [
    "1. تمام ویژگی‌های حتی جزئی ربات رو بنویسید ❗️",
    "2. نیاز به پنل ادمین درون ربات دارین یا خیر (روی قیمت ربات تأثیر مستقیم خواهد داشت)⁉️",
    "3. در مورد ساخت ربات از بات‌فادر (دریافت API Token و ...) اطلاع دارین ⁉️",
    "4. ربات رو می‌تونید روی هاست یا سرور اجرا کنید ‼️",
    "5. هاست یا سرور رو از مجموعه ما می‌خرید؟",
    "6. سورس کد رو دریافت می‌کنید یا که خود ادمین ربات رو برای شما اجرا کنه؟",
    "7. نوع پرداخت رو هم مشخص کنید (ارزی یا تومانی) ❗️"
]

async def ask_question(event, user_id):
    user_data = messages_db["users"].get(user_id)
    if user_data is None:
        return

    current_question = user_data["current_question"]

    if current_question < len(questions):
        await event.respond(questions[current_question])
    else:
        await show_summary(event, user_id)

@client.on(events.NewMessage)
async def handle_answer(event):
    user_id = event.sender_id
    user_data = messages_db["users"].get(user_id)

    if user_data and user_data["current_question"] < len(questions):
        answer = event.raw_text
        user_data["answers"].append(answer)
        user_data["current_question"] += 1
        save_database(messages_db)

        if user_data["current_question"] < len(questions):
            await ask_question(event, user_id)
        else:
            await show_summary(event, user_id)

@client.on(events.NewMessage(pattern=r'/start'))
async def start(event):
    user_id = event.sender_id
    if user_id == ADMIN_ID:
        buttons = [[Button.inline("📋 پنل ادمین", b"admin_panel")]]
        await event.respond("به ربات خوش آمدید. این بخش مخصوص ادمین است.", buttons=buttons)
    else:
        if str(user_id) not in messages_db["users"]:
            messages_db["users"][str(user_id)] = {
                "username": event.sender.username or "ناشناس",
                "answers": [],
                "current_question": 0
            }
            save_database(messages_db)
        
        buttons = [[Button.inline("✅ شروع", b"start_questions"), Button.inline("❌ لغو", b"cancel")]]
        await event.respond("مایل هستید به سوالات پاسخ دهید؟", buttons=buttons)

@client.on(events.CallbackQuery)
async def callback_handler(event):
    user_id = event.sender_id
    user_data = messages_db["users"].get(str(user_id))

    if event.data == b"start_questions":
        if not user_data:  # If user is not registered yet
            messages_db["users"][str(user_id)] = {
                "username": event.sender.username or "ناشناس",
                "answers": [],
                "current_question": 0
            }
            save_database(messages_db)

        user_data = messages_db["users"].get(str(user_id))
        if user_data["current_question"] < len(questions):
            await ask_question(event, str(user_id))
        else:
            await event.respond("❗️ شما قبلاً به تمام سوالات پاسخ داده‌اید.")
    elif event.data == b"cancel":
        await event.respond("❌ پاسخگویی به سوالات لغو شد.")
    elif event.data == b"admin_panel" and user_id == ADMIN_ID:
        buttons = [
            [Button.inline("📩 پیام‌های جدید", b"unread")],
            [Button.inline("✅ پاسخ داده شده", b"responded")],
        ]
        await event.edit("پنل ادمین:\nیکی از گزینه‌ها را انتخاب کنید.", buttons=buttons)

async def ask_question(event, user_id):
    user_data = messages_db["users"].get(user_id)
    if not user_data:
        return

    current_question = user_data["current_question"]
    if current_question < len(questions):
        await event.respond(questions[current_question])
        user_data["current_question"] += 1
        save_database(messages_db)
    else:
        await show_summary(event, user_id)

async def show_summary(event, user_id):
    user_data = messages_db["users"].get(str(user_id), None)
    if not user_data:
        return

    answers = user_data["answers"]
    summary = "\n".join([f"{i+1}. {questions[i]} {answers[i]}" for i in range(len(answers))])
    buttons = [[Button.inline("✅ تایید", b"confirm"), Button.inline("❌ حذف", b"delete")]]
    await event.respond(f"نتایج نهایی:\n\n{summary}", buttons=buttons)

@client.on(events.NewMessage)
async def handle_answer(event):
    user_id = event.sender_id
    user_data = messages_db["users"].get(str(user_id), None)

    if user_data and user_data["current_question"] <= len(questions):
        answer = event.raw_text
        user_data["answers"].append(answer)
        save_database(messages_db)

        if user_data["current_question"] < len(questions):
            await ask_question(event, user_id)
        else:
            await show_summary(event, user_id)

async def ask_question(event, user_id):
    if user_id not in user_data or 'current_question' not in user_data[user_id]:
        return

    current_question = user_data[user_id]['current_question']
    if current_question < len(questions):
        await event.respond(questions[current_question])
        user_data[user_id]['current_question'] += 1
    else:
        await show_summary(event, user_id)

@client.on(events.NewMessage)
async def handle_answer(event):
    user_id = event.sender_id
    username = event.sender.username

    if user_id in user_data and 'current_question' in user_data[user_id]:
        current_question = user_data[user_id]['current_question'] - 1
        if current_question < len(questions):
            user_data[user_id]['answers'].append(event.raw_text)
            log_user_data(user_id, username, questions[current_question], event.raw_text)
            if current_question + 1 < len(questions):
                await ask_question(event, user_id)
            else:
                await show_summary(event, user_id)
        elif event.file:  # Handle file inputs
            file_id = event.file.id
            log_user_data(user_id, username, "File", file_id)
            await event.respond("✅ فایل شما دریافت شد.")

async def show_summary(event, user_id):
    answers = user_data[user_id]['answers']
    summary = "\n".join([f"{i+1}. {questions[i]} {answers[i]}" for i in range(len(questions))])
    buttons = [
        [Button.inline("✅ تایید", b"confirm"), Button.inline("❌ حذف", b"delete")]
    ]
    await event.respond(f"نتایج نهایی:\n\n{summary}", buttons=buttons)

@client.on(events.CallbackQuery)
async def final_handler(event):
    user_id = event.sender_id

    if event.data == b"confirm":
        answers = user_data.get(user_id, {}).get('answers', [])
        summary = "\n".join([f"{i+1}. {questions[i]} {answers[i]}" for i in range(len(questions))])
        await client.send_message(ADMIN_ID, f"پاسخ‌های کاربر {user_id}:\n\n{summary}")
        await event.edit("✅ پیام به ادمین ارسال شد. ممنون از همکاری شما!")
        user_data.pop(user_id, None)
    elif event.data == b"delete":
        await event.edit("❌ پاسخ‌ها حذف شدند!")
        user_data.pop(user_id, None)

def log_user_data(user_id, username, question, answer):
    """Logs the user's data into an Excel file and prints it."""
    print(f"User ID: {user_id}, Username: {username}, Question: {question}, Answer: {answer}")

    # Save data to Excel
    df = pd.read_excel(excel_file)
    new_row = {"User ID": user_id, "Username": username, "Question": question, "Answer": answer, "File ID": ""}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(excel_file, index=False)

async def show_summary(event, user_id):
    user_data = messages_db["users"].get(user_id)
    if user_data is None:
        return

    summary = "\n".join(
        [f"{i+1}. {questions[i]}: {user_data['answers'][i]}" for i in range(len(user_data["answers"]))]
    )
    buttons = [
        [Button.inline("✅ تایید", f"confirm_{user_id}"), Button.inline("❌ حذف", f"delete_{user_id}")]
    ]
    await event.respond(f"نتایج نهایی:\n\n{summary}", buttons=buttons)

@client.on(events.CallbackQuery)
async def admin_panel(event):
    user_id = event.sender_id

    if user_id == ADMIN_ID:
        if event.data == b"admin_panel":
            buttons = [
                [Button.inline("⏳ در انتظار پاسخ", b"waiting_reply")],
                [Button.inline("✅ پاسخ داده شده", b"responded")],
                [Button.inline("📩 خوانده نشده", b"unread")],
            ]
            await event.edit("پنل ادمین:\nبخش مورد نظر را انتخاب کنید:", buttons=buttons)

        elif event.data == b"unread":
            await display_messages(event, "unread")

        elif event.data == b"waiting_reply":
            await display_messages(event, "waiting")

        elif event.data == b"responded":
            await display_messages(event, "responded")

        elif event.data.decode().startswith("confirm_"):
            target_user = int(event.data.decode().split("_")[1])
            answers = messages_db["users"][target_user]["answers"]

            summary = "\n".join(
                [f"{i+1}. {questions[i]}: {answers[i]}" for i in range(len(answers))]
            )
            await client.send_message(ADMIN_ID, f"پاسخ‌های کاربر {target_user}:\n\n{summary}")
            await event.edit("✅ پاسخ‌ها به ادمین ارسال شدند!")

        elif event.data.decode().startswith("delete_"):
            target_user = int(event.data.decode().split("_")[1])
            messages_db["users"].pop(target_user, None)
            save_database(messages_db)
            await event.edit("❌ پاسخ‌ها حذف شدند.")

async def display_messages(event, section):
    """Display messages for a specific section to the admin."""
    if messages_db[section]:
        buttons = [
            [Button.inline(f"{msg['username']} - {msg['message'][:20]}", f"respond_{section}_{i}")]
            for i, msg in enumerate(messages_db[section])
        ]
        buttons.append([Button.inline("🔙 بازگشت", b"admin_panel")])
        await event.edit(f"📋 بخش: {section}\n\nپیام‌های موجود:", buttons=buttons)
    else:
        await event.edit(f"📋 بخش: {section}\n\nهیچ پیامی در این بخش وجود ندارد.", buttons=[[Button.inline("🔙 بازگشت", b"admin_panel")]])

print("ربات در حال اجرا است...")
client.run_until_disconnected()
