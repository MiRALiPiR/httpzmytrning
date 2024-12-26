import os

from dotenv import load_dotenv
from telethon import Button, TelegramClient, events
from telethon.tl.custom.message import Message

load_dotenv()

API_ID = os.getenv('api_id')
API_HASH = os.getenv('api_hash')
TOKEN = os.getenv('token')
client = TelegramClient('bot_session', api_id=API_ID, api_hash=API_HASH ).start(bot_token=TOKEN)

@client.on(events.NewMessage(pattern=r'/start'))
async def start(event: Message):
    await event.respond('Hi Babe')

client.run_until_disconnected()