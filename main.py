import os
from pyrogram import Client
from modules.tiktok import register_tiktok

API_ID = int(os.getenv("API_ID", "5047271"))
API_HASH = os.getenv("API_HASH", "047d9ed308172e637d4265e1d9ef0c27")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7896090354:AAG16U8-FaR2cMxzROcTvOAwePaBmkcG-QU")

app = Client(
    "social_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Register modules
register_tiktok(app)

print("🚀 Social Media Downloader Bot started...")

app.run()
