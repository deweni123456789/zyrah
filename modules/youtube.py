import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL

ydl_opts_video = {
    "format": "best",
    "quiet": True,
    "outtmpl": "%(id)s.%(ext)s"
}

ydl_opts_audio = {
    "format": "bestaudio/best",
    "quiet": True,
    "outtmpl": "%(id)s.%(ext)s",
    "postprocessors": [{"key": "FFmpegExtractAudio","preferredcodec": "mp3","preferredquality": "192"}]
}

def register_youtube(app: Client):
    @app.on_message(filters.private & filters.regex(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/\S+"))
    async def youtube_handler(client, message):
        url = message.text.strip()
        msg = await message.reply("⏳ Select download option...")
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📹 Download Video", callback_data=f"video|{url}")],
            [InlineKeyboardButton("🎵 Download Audio", callback_data=f"audio|{url}")],
            [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]
        ])
        await msg.edit("Choose an option:", reply_markup=buttons)

    @app.on_callback_query()
    async def button_click(client: Client, callback: CallbackQuery):
        option, url = callback.data.split("|")
        downloading_msg = await callback.message.reply("⏳ Downloading...")

        try:
            ydl_opts = ydl_opts_video if option=="video" else ydl_opts_audio
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                if option=="audio":
                    file_path = os.path.splitext(file_path)[0] + ".mp3"

            if option=="audio":
                await client.send_audio(chat_id=callback.message.chat.id, audio=file_path,
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]]))
            else:
                await client.send_video(chat_id=callback.message.chat.id, video=file_path,
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]]))
            await downloading_msg.delete()
            await callback.message.delete()
            os.remove(file_path)

        except Exception as e:
            await downloading_msg.edit(f"⚠️ Error: {e}")
