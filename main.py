import os, sys
from pyrogram import Client
from modules.tiktok import register_tiktok
from modules.youtube import register_youtube

API_ID = os.getenv("5047271")
API_HASH = os.getenv("047d9ed308172e637d4265e1d9ef0c27")
BOT_TOKEN = os.getenv("7896090354:AAFhFhcbEoJreu1vUZN-kY673pJqV62eMoU")

if not all([API_ID, API_HASH, BOT_TOKEN]):
    print("❌ Missing API_ID / API_HASH / BOT_TOKEN")
    sys.exit(1)

API_ID = int(API_ID)

app = Client(
    "social_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Register modules
register_tiktok(app)
register_youtube(app)

app.start()
print("🚀 Social Media Downloader Bot started...")
app.idle()

