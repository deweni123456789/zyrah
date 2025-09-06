import io
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
import datetime

ydl_opts = {
    "format": "best",
    "outtmpl": "%(id)s.%(ext)s",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
}

def register_tiktok(app: Client):
    @app.on_message(filters.private & filters.regex(r"(https?://)?(www\.)?tiktok\.com/\S+"))
    async def tiktok_handler(client, message):
        url = message.text.strip()
        processing_msg = await message.reply("⏳ Downloading TikTok video... Please wait")

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            # Metadata
            title = info.get("title", "N/A")
            uploader = info.get("uploader", "N/A")
            upload_date = info.get("upload_date", "N/A")
            if upload_date != "N/A":
                upload_date = datetime.datetime.strptime(upload_date, "%Y%m%d").strftime("%Y-%m-%d")
            duration = info.get("duration", 0)
            view_count = info.get("view_count", 0)
            like_count = info.get("like_count", 0)
            comment_count = info.get("comment_count", 0)

            caption = (
                f"🎬 Title: {title}\n"
                f"👤 Author: {uploader}\n"
                f"📅 Uploaded: {upload_date}\n"
                f"⏱ Duration: {duration}s\n"
                f"👁 Views: {view_count} | 👍 Likes: {like_count} | 💬 Comments: {comment_count}"
            )

            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("Download Video", url=url)],
                [InlineKeyboardButton("Download Audio", url=url)],
                [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]
            ])

            await processing_msg.delete()
            await client.send_message(chat_id=message.chat.id, text=caption, reply_markup=buttons)

        except Exception as e:
            await processing_msg.edit(f"⚠️ Error while downloading: {e}")
