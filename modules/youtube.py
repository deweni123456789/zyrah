import os
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Cookies file path (inside your container/project)
COOKIES_PATH = "/app/cookies.txt"

# Store URLs for buttons
URL_STORE = {}

def register_youtube(app: Client):
    @app.on_message(filters.private & filters.regex(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/\S+"))
    async def youtube_handler(client, message):
        url = message.text.strip()

        # Inline buttons for download
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🎥 Download Video", callback_data=f"video|{url}"),
                    InlineKeyboardButton("🎵 Download Audio", callback_data=f"audio|{url}")
                ]
            ]
        )

        sent = await message.reply_text("Choose download option ⬇️", reply_markup=buttons)
        URL_STORE[(sent.chat.id, sent.id)] = url

    @app.on_callback_query(filters.regex(r"^(video|audio)\|"))
    async def button_click(client, callback):
        option, url = callback.data.split("|", 1)

        await callback.message.edit_text("⚡ Downloading, please wait...")

        try:
            if option == "video":
                ydl_opts = {
                    "format": "best",
                    "outtmpl": "%(title)s.%(ext)s",
                    "cookies": COOKIES_PATH,
                }
            else:  # audio
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": "%(title)s.%(ext)s",
                    "cookies": COOKIES_PATH,
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

                if option == "audio":
                    file_path = os.path.splitext(file_path)[0] + ".mp3"

            # Upload file
            await callback.message.reply_document(file_path, caption=f"✅ Downloaded: {info.get('title')}")
            await callback.message.delete()

        except Exception as e:
            await callback.message.edit_text(f"⚠️ Error: {str(e)}")
