import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL
import datetime

# Path to cookies file (exported from your browser)
COOKIES_FILE = "cookies.txt"  # place this in project root

# Video download options
ydl_opts_video = {
    "format": "best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "cookiefile": COOKIES_FILE,
    "outtmpl": "%(id)s.%(ext)s"
}

# Audio download options
ydl_opts_audio = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "cookiefile": COOKIES_FILE,
    "outtmpl": "%(id)s.%(ext)s",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192"
    }]
}

def register_youtube(app: Client):
    @app.on_message(filters.private & filters.regex(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/\S+"))
    async def youtube_handler(client, message):
        url = message.text.strip()
        fetching_msg = await message.reply("⏳ Fetching YouTube info... Please wait")

        try:
            with YoutubeDL(ydl_opts_video) as ydl:
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
            requester = message.from_user.mention

            caption = (
                f"🎬 Title: {title}\n\n"
                f"👁 Views: {view_count}\n"
                f"👍 Likes: {like_count}\n"
                f"💬 Comments: {comment_count}\n"
                f"👤 Channel: {uploader}\n"
                f"📅 Uploaded: {upload_date}\n"
                f"⏱ Duration: {duration}s\n\n"
                f"Requested by: {requester}"
            )

            # Inline buttons
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("📹 Download Video", callback_data=f"video|{url}")],
                [InlineKeyboardButton("🎵 Download Audio", callback_data=f"audio|{url}")],
                [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]
            ])

            select_msg = await message.reply("Select download option:", reply_markup=buttons)
            await fetching_msg.delete()  # Delete fetching message

        except Exception as e:
            await fetching_msg.edit(f"⚠️ Error while fetching info: {e}")

    @app.on_callback_query()
    async def button_click(client: Client, callback: CallbackQuery):
        data = callback.data
        option, url = data.split("|")
        downloading_msg = await callback.message.reply("⏳ Downloading... Please wait")

        try:
            if option == "video":
                ydl_opts = ydl_opts_video
            elif option == "audio":
                ydl_opts = ydl_opts_audio
            else:
                await downloading_msg.edit("❌ Unknown option")
                return

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                if option == "audio":
                    file_path = os.path.splitext(file_path)[0] + ".mp3"

            # Caption
            title = info.get("title", "N/A")
            uploader = info.get("uploader", "N/A")
            upload_date = info.get("upload_date", "N/A")
            if upload_date != "N/A":
                upload_date = datetime.datetime.strptime(upload_date, "%Y%m%d").strftime("%Y-%m-%d")
            duration = info.get("duration", 0)
            view_count = info.get("view_count", 0)
            like_count = info.get("like_count", 0)
            comment_count = info.get("comment_count", 0)
            requester = callback.from_user.mention

            caption = (
                f"🎬 Title: {title}\n\n"
                f"👁 Views: {view_count}\n"
                f"👍 Likes: {like_count}\n"
                f"💬 Comments: {comment_count}\n"
                f"👤 Channel: {uploader}\n"
                f"📅 Uploaded: {upload_date}\n"
                f"⏱ Duration: {duration}s\n\n"
                f"Requested by: {requester}"
            )

            # Send file
            if option == "audio":
                await client.send_audio(
                    chat_id=callback.message.chat.id,
                    audio=file_path,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]])
                )
            else:
                await client.send_video(
                    chat_id=callback.message.chat.id,
                    video=file_path,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]])
                )

            # Clean messages
            await downloading_msg.delete()
            if callback.message.reply_markup:
                await callback.message.delete()

            # Remove temp file
            os.remove(file_path)

        except Exception as e:
            await downloading_msg.edit(f"⚠️ Error while downloading: {e}")
