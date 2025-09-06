import os
import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait
from modules.tiktok import register_tiktok
from modules.youtube import register_youtube
# from modules.youtube import register_youtube  # YouTube optional

API_ID = int(os.getenv("API_ID", "5047271"))
API_HASH = os.getenv("API_HASH", "047d9ed308172e637d4265e1d9ef0c27"))
BOT_TOKEN = os.getenv("BOT_TOKEN", "7896090354:AAFhFhcbEoJreu1vUZN-kY673pJqV62eMoU")

app = Client(
    "social_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Register modules
register_tiktok(app)
register_youtube(app)
# register_youtube(app)  # Optional

async def run_bot():
    while True:
        try:
            print("🚀 Bot starting...")
            await app.start()
            print("✅ Bot started. Waiting for messages...")
            await app.idle()
        except FloodWait as e:
            wait_time = e.value
            print(f"⚠️ FloodWait detected. Waiting {wait_time} seconds before retry...")
            await asyncio.sleep(wait_time)
        except Exception as ex:
            print(f"❌ Unexpected error: {ex}")
            print("🔁 Restarting bot in 5 seconds...")
            await asyncio.sleep(5)
        finally:
            await app.stop()
            print("🔄 Bot stopped. Restarting loop...")

if __name__ == "__main__":
    asyncio.run(run_bot())
