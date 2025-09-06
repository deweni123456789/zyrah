import os
from dotenv import load_dotenv
from pyrogram import Client
from modules.tiktok import register_tiktok
from modules.youtube import register_youtube

load_dotenv()  # Load .env file

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client(
    "social_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

register_tiktok(app)
register_youtube(app)


print("🚀 Social Media Downloader Bot started...")
app.run()

