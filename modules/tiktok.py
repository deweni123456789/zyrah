import os
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Example free TikTok API endpoint (TikMate or self-hosted)
TIKTOK_API = os.getenv("TIKTOK_API", "https://tikmate.app/api/lookup?url=")

def register_tiktok(app: Client):
    @app.on_message(filters.private & filters.regex(r"(https?://)?(www\.)?tiktok\.com/\S+"))
    async def tiktok_handler(client, message):
        url = message.text.strip()
        await message.reply("⏳ Processing TikTok link...")

        try:
            response = requests.get(f"{TIKTOK_API}{url}").json()
            
            if not response or "video" not in response:
                await message.reply("❌ Failed to fetch video info. Try another link.")
                return

            # Metadata
            data = response["video"]
            title = data.get("title", "N/A")
            uploader = data.get("author", "N/A")
            upload_date = data.get("create_time", "N/A")
            likes = data.get("like_count", "N/A")
            comments = data.get("comment_count", "N/A")
            shares = data.get("share_count", "N/A")
            duration = data.get("duration", "N/A")

            caption = (
                f"🎬 Title: {title}\n"
                f"👤 Author: {uploader}\n"
                f"📅 Uploaded: {upload_date}\n"
                f"⏱ Duration: {duration}s\n"
                f"👍 Likes: {likes} | 💬 Comments: {comments} | 🔄 Shares: {shares}"
            )

            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("Without Watermark", url=data.get("play", url))],
                [InlineKeyboardButton("With Watermark", url=data.get("wmplay", url))],
                [InlineKeyboardButton("Audio Only", url=data.get("audio", url))],
                [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]
            ])

            # Send video (without downloading to server)
            await client.send_message(
                chat_id=message.chat.id,
                text=caption,
                reply_markup=buttons
            )

        except Exception as e:
            await message.reply(f"⚠️ Error while downloading: {e}")
