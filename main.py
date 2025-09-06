import os
from pyrogram import Client
from modules.tiktok import register_tiktok
from modules.youtube import register_youtube

# ⚠️ Using your credentials directly
API_ID = 5047271
API_HASH = "047d9ed308172e637d4265e1d9ef0c27"
BOT_TOKEN = "7896090354:AAFhFhcbEoJreu1vUZN-kY673pJqV62eMoU"

app = Client(
    "social_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Register modules
register_tiktok(app)
register_youtube(app)

print("🚀 Social Media Downloader Bot started...")

app.run()
