import os
import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait
from modules.tiktok import register_tiktok

API_ID = int(os.getenv("5047271"))
API_HASH = os.getenv("047d9ed308172e637d4265e1d9ef0c27")
BOT_TOKEN = os.getenv("7896090354:AAFhFhcbEoJreu1vUZN-kY673pJqV62eMoU")

app = Client("social_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
register_tiktok(app)

async def run_bot():
    while True:
        try:
            print("🚀 Bot starting...")
            await app.start()
            print("✅ Bot started.")
            await app.idle()
        except FloodWait as e:
            wait_time = e.value
            print(f"⚠️ FloodWait detected. Waiting {wait_time}s...")
            await asyncio.sleep(wait_time)
        except Exception as ex:
            print(f"❌ Unexpected error: {ex}")
            await asyncio.sleep(5)
        finally:
            await app.stop()
            print("🔄 Restarting bot...")

if __name__ == "__main__":
    asyncio.run(run_bot())
