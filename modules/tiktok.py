import os
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# TikTok free API endpoint (self-hosted BOTCAHX/tiktokdl-api)
# Example: https://your-deployment-url.vercel.app/tiktok/api.php?url=
TIKTOK_API = os.getenv("TIKTOK_API", "https://tikdown.vercel.app/tiktok/api.php")

def register_tiktok(app: Client):
    @app.on_message(filters.private & filters.regex(r"(https?://)?(www\.)?tiktok\.com/\S+"))
    async def tiktok_handler(client, message):
        url = message.text.strip()
        await message.reply("⏳ Downloading TikTok video... Please wait")

        try:
            api_url = f"{TIKTOK_API}?url={url}"
            response = requests.get(api_url).json()

            if "video" in response:
                video_url = response["video"]

                await client.send_video(
                    chat_id=message.chat.id,
                    video=video_url,
                    caption=(
                        f"✅ TikTok Downloaded\n\n"
                        f"🎥 Title: {response.get('title','N/A')}\n"
                        f"👤 Author: {response.get('author','N/A')}"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]]
                    )
                )
            else:
                await message.reply("❌ Could not download TikTok video. Please try another link.")

        except Exception as e:
            await message.reply(f"⚠️ Error while downloading: {e}")
