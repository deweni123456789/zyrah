import os
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

URL_STORE = {}

def register_instagram(app: Client):
    # Command handler (/insta link)
    @app.on_message(filters.command("insta") & filters.private)
    async def insta_cmd(client, message):
        if len(message.command) < 2:
            return await message.reply_text("⚠️ Please provide an Instagram link.\n\nUsage: `/insta <link>`")

        url = message.command[1].strip()
        await send_insta_buttons(message, url)

    # Auto-detect Instagram links
    @app.on_message(filters.private & filters.regex(r"(https?://)?(www\.)?(instagram\.com|instagr\.am)/\S+"))
    async def insta_autodetect(client, message):
        url = message.text.strip()
        await send_insta_buttons(message, url)

    async def send_insta_buttons(message, url):
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🎥 Download Video", callback_data=f"insta_video|{url}"),
                    InlineKeyboardButton("🎵 Download Audio", callback_data=f"insta_audio|{url}")
                ]
            ]
        )
        sent = await message.reply_text("📲 Instagram link detected!\nChoose an option ⬇️", reply_markup=buttons)
        URL_STORE[(sent.chat.id, sent.id)] = url

    # Handle button clicks
    @app.on_callback_query(filters.regex(r"^(insta_video|insta_audio)\|"))
    async def insta_button(client, callback):
        option, url = callback.data.split("|", 1)
        await callback.message.edit_text("⚡ Downloading from Instagram...")

        try:
            if option == "insta_video":
                ydl_opts = {
                    "format": "best",
                    "outtmpl": "%(title)s.%(ext)s",
                }
            else:
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": "%(title)s.%(ext)s",
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

                if option == "insta_audio":
                    file_path = os.path.splitext(file_path)[0] + ".mp3"

            # Metadata
            caption = (
                f"✅ **Downloaded Successfully**\n\n"
                f"**Title:** {info.get('title', 'N/A')}\n"
                f"**Uploader:** {info.get('uploader', 'N/A')}\n"
                f"**Likes:** {info.get('like_count', 'N/A')}\n"
                f"**Views:** {info.get('view_count', 'N/A')}\n"
                f"**Duration:** {info.get('duration', 'N/A')} sec\n"
                f"👤 **Requested by:** {callback.from_user.mention}"
            )

            # Upload file
            await callback.message.reply_document(file_path, caption=caption)

            # Delete "Downloading..." message
            await callback.message.delete()

        except Exception as e:
            await callback.message.edit_text(f"⚠️ Error: {str(e)}")
