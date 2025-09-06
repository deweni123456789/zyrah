import os
import re
import tempfile
import asyncio
from functools import partial
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL

# store message_id -> url for callbacks
URL_STORE = {}

# yt-dlp options base
def get_ydl_opts(is_audio=False, cookies_path=None):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "outtmpl": os.path.join(tempfile.gettempdir(), "%(title)s.%(ext)s"),
    }
    if is_audio:
        opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        opts["format"] = "bestvideo+bestaudio/best"
    if cookies_path and os.path.exists(cookies_path):
        opts["cookiefile"] = cookies_path
    return opts

def download_with_ytdlp(url, is_audio=False, cookies_path=None):
    opts = get_ydl_opts(is_audio, cookies_path)
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        # if audio, extension changed to .mp3
        if is_audio:
            base, _ = os.path.splitext(file_path)
            file_path = base + ".mp3"
        return file_path, info

async def run_blocking(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args))

def register_youtube(app: Client):
    @app.on_message(filters.private & filters.regex(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/\S+"))
    async def youtube_handler(client, message):
        url = message.text.strip()
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📹 Download Video", callback_data="yt_video")],
            [InlineKeyboardButton("🎵 Download Audio", callback_data="yt_audio")],
            [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]
        ])
        sent = await message.reply("Choose download option:", reply_markup=buttons)
        URL_STORE[(sent.chat.id, sent.message_id)] = url

    @app.on_callback_query(filters.regex("^yt_"))
    async def callback_handler(client, callback: CallbackQuery):
        key = (callback.message.chat.id, callback.message.message_id)
        url = URL_STORE.get(key)
        if not url:
            await callback.answer("Expired or missing URL. Please send the link again.", show_alert=True)
            return

        is_audio = callback.data == "yt_audio"
        await callback.message.edit("⏳ Downloading, please wait...")

        cookies_path = os.path.join(os.getcwd(), "cookies.txt")  # optional
        try:
            file_path, info = await run_blocking(download_with_ytdlp, url, is_audio, cookies_path)
        except Exception as e:
            await callback.message.edit(f"❌ Download failed: {e}")
            return

        title = info.get("title", "YouTube")
        try:
            if is_audio:
                await client.send_audio(
                    chat_id=callback.message.chat.id,
                    audio=file_path,
                    title=title,
                    performer=info.get("uploader"),
                    caption=f"🎵 {title}\n👤 Requested by {callback.from_user.mention}"
                )
            else:
                await client.send_video(
                    chat_id=callback.message.chat.id,
                    video=file_path,
                    caption=f"🎬 {title}\n👤 Requested by {callback.from_user.mention}"
                )
            await callback.message.delete()
        finally:
            try:
                os.remove(file_path)
            except:
                pass
            URL_STORE.pop(key, None)
