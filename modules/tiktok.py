import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL
import datetime

# FFmpeg must be installed in container/Docker
# TikTok download options
ydl_opts_video = {
    "format": "best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "outtmpl": "%(id)s.%(ext)s"
}

ydl_opts_audio = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "outtmpl": "%(id)s.%(ext)s",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192"
    }]
}

def register_tiktok(app: Client):
    @app.on_message(filters.private & filters.regex(r"(https?://)?(www\.)?tiktok\.com/\S+"))
    async def tiktok_handler(client, message):
        url = message.text.strip()
        fetching_msg = await message.reply("⏳ Fetching TikTok info... Please wait")

        try:
            with YoutubeDL(ydl_opts_video) as ydl:
                info = ydl.extract_info(url, download=False)

            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("With Watermark", callback_data=f"wm|{url}")],
                [InlineKeyboardButton("Without Watermark", callback_data=f"nowm|{url}")],
                [InlineKeyboardButton("Audio Only", callback_data=f"audio|{url}")],
                [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]
            ])

            await message.reply("Select download option:", reply_markup=buttons)
            await fetching_msg.delete()

        except Exception as e:
            await fetching_msg.edit(f"⚠️ Error while fetching info: {e}")

    @app.on_callback_query()
    async def button_click(client: Client, callback: CallbackQuery):
        option, url = callback.data.split("|")
        downloading_msg = await callback.message.reply("⏳ Downloading... Please wait")

        try:
            ydl_opts = ydl_opts_video if option in ["wm", "nowm"] else ydl_opts_audio

            # Set filename for no watermark
            if option == "nowm":
                ydl_opts = ydl_opts_video.copy()
                ydl_opts["outtmpl"] = "%(id)s_no_watermark.%(ext)s"

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                if option == "audio":
                    file_path = os.path.splitext(file_path)[0] + ".mp3"

            # Metadata caption
            title = info.get("title", "N/A")
            uploader = info.get("uploader", "N/A")
            duration = info.get("duration", 0)
            view_count = info.get("view_count", 0)
            like_count = info.get("like_count", 0)
            comment_count = info.get("comment_count", 0)
            shares = info.get("share_count", 0)
            requester = callback.from_user.mention

            caption = (
                f"🎬 Title: {title}\n\n"
                f"👁 Views: {view_count}\n"
                f"👍 Likes: {like_count}\n"
                f"💬 Comments: {comment_count}\n"
                f"🔄 Shares: {shares}\n\n"
                f"👤 Author: {uploader}\n"
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

            # Cleanup
            await downloading_msg.delete()
            if callback.message.reply_markup:
                await callback.message.delete()
            os.remove(file_path)

        except Exception as e:
            await downloading_msg.edit(f"⚠️ Error while downloading: {e}")
