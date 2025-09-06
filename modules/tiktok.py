import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL
import datetime

# Video download options
ydl_opts_video = {
    "format": "best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "outtmpl": "%(id)s.%(ext)s"
}

# Audio download options with postprocessor to ensure audio file
ydl_opts_audio = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "outtmpl": "%(id)s.%(ext)s",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }]
}

def register_tiktok(app: Client):
    @app.on_message(filters.private & filters.regex(r"(https?://)?(www\.)?tiktok\.com/\S+"))
    async def tiktok_handler(client, message):
        url = message.text.strip()
        processing_msg = await message.reply("⏳ Fetching TikTok info... Please wait")

        try:
            with YoutubeDL(ydl_opts_video) as ydl:
                info = ydl.extract_info(url, download=False)

            # Metadata
            requester = message.from_user.mention
            title = info.get("title", "N/A")
            uploader = info.get("uploader", "N/A")
            upload_date = info.get("upload_date", "N/A")
            if upload_date != "N/A":
                upload_date = datetime.datetime.strptime(upload_date, "%Y%m%d").strftime("%Y-%m-%d")
            duration = info.get("duration", 0)
            view_count = info.get("view_count", 0)
            like_count = info.get("like_count", 0)
            comment_count = info.get("comment_count", 0)
            shares = info.get("share_count", 0)

            # Caption: requester top line
            caption = (
                f"🎬 Title: {title}\n"
                f"👁 Views: {view_count}\n"
                f"👍 Likes: {like_count}\n"
                f"💬 Comments: {comment_count}\n"
                f"🔄 Shares: {shares}\n\n"
                f"👤 Author: {uploader}\n"
                f"📅 Uploaded: {upload_date}\n"
                f"⏱ Duration: {duration}s"

                f"Requested by: {requester}\n\n"
            )

            # Inline buttons
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("With Watermark", callback_data=f"wm|{url}")],
                [InlineKeyboardButton("Without Watermark", callback_data=f"nowm|{url}")],
                [InlineKeyboardButton("Audio Only", callback_data=f"audio|{url}")],
                [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]
            ])

            await processing_msg.delete()
            await message.reply("Select download option:", reply_markup=buttons)

        except Exception as e:
            await processing_msg.edit(f"⚠️ Error while fetching info: {e}")

    @app.on_callback_query()
    async def button_click(client: Client, callback: CallbackQuery):
        data = callback.data
        option, url = data.split("|")
        processing = await callback.message.reply("⏳ Downloading... Please wait")

        try:
            if option == "wm":
                ydl_opts = ydl_opts_video
            elif option == "nowm":
                ydl_opts = ydl_opts_video.copy()
                ydl_opts["outtmpl"] = "%(id)s_no_watermark.%(ext)s"
            elif option == "audio":
                ydl_opts = ydl_opts_audio
            else:
                await processing.edit("❌ Unknown option")
                return

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                if option == "audio":
                    file_path = os.path.splitext(file_path)[0] + ".mp3"

            # Send file with caption
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

            await processing.delete()
            os.remove(file_path)

        except Exception as e:
            await processing.edit(f"⚠️ Error while downloading: {e}")
