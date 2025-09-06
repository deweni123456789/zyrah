from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from TikTokApi import TikTokApi
import datetime

api = TikTokApi.get_instance()

def register_tiktok(app: Client):
    @app.on_message(filters.private & filters.regex(r"(https?://)?(www\.)?tiktok\.com/\S+"))
    async def tiktok_handler(client, message):
        url = message.text.strip()
        await message.reply("⏳ Processing TikTok link... Please wait")

        try:
            video_data = api.video(url=url)

            # Download bytes
            video_bytes = video_data.bytes()
            video_no_watermark_bytes = video_data.bytes(no_watermark=True)
            audio_bytes = video_data.bytes(audio=True)

            # Metadata
            info = video_data.info()
            title = info.get("desc", "N/A")
            author = info.get("author", {}).get("uniqueId", "N/A")
            upload_time = datetime.datetime.fromtimestamp(info.get("createTime", 0))
            duration = info.get("video", {}).get("duration", 0)
            stats = info.get("stats", {})
            likes = stats.get("diggCount", 0)
            comments = stats.get("commentCount", 0)
            shares = stats.get("shareCount", 0)

            caption = (
                f"🎬 Title: {title}\n"
                f"👤 Author: {author}\n"
                f"📅 Uploaded: {upload_time}\n"
                f"⏱ Duration: {duration}s\n"
                f"👍 Likes: {likes} | 💬 Comments: {comments} | 🔄 Shares: {shares}"
            )

            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("Without Watermark", url="https://tiktok.com")],
                [InlineKeyboardButton("With Watermark", url="https://tiktok.com")],
                [InlineKeyboardButton("Audio Only", url="https://tiktok.com")],
                [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]
            ])

            # Send files
            await client.send_video(chat_id=message.chat.id, video=video_no_watermark_bytes, caption=caption)
            await client.send_video(chat_id=message.chat.id, video=video_bytes)
            await client.send_audio(chat_id=message.chat.id, audio=audio_bytes)

        except Exception as e:
            await message.reply(f"⚠️ Error while downloading: {e}")
