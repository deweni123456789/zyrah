import os
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Function to fetch download links from SaveFrom.net
def get_savefrom_links(youtube_url):
    api_url = "https://worker.sf-api.com/savefrom.php"  # unofficial API
    params = {"url": youtube_url, "r": "user"}
    r = requests.get(api_url, params=params)
    data = r.json()
    links = []
    for item in data.get("url", []):
        links.append({
            "quality": item.get("quality"),
            "type": item.get("type"),
            "link": item.get("url")
        })
    return links

def register_youtube(app: Client):
    @app.on_message(filters.private & filters.regex(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/\S+"))
    async def youtube_handler(client, message):
        url = message.text.strip()
        fetching_msg = await message.reply("⏳ Fetching YouTube info... Please wait")

        try:
            links = get_savefrom_links(url)
            if not links:
                await fetching_msg.edit("⚠️ Unable to fetch download links")
                return

            # Choose best video and audio links
            video_link = next((l["link"] for l in links if "video" in l["type"]), None)
            audio_link = next((l["link"] for l in links if "audio" in l["type"]), None)

            # Metadata (simple, without API)
            title = url.split("/")[-1]  # fallback as we can't get real title without cookies
            requester = message.from_user.mention
            caption = f"🎬 Title: {title}\nRequested by: {requester}"

            # Inline buttons
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("📹 Download Video", callback_data=f"video|{video_link}")],
                [InlineKeyboardButton("🎵 Download Audio", callback_data=f"audio|{audio_link}")],
                [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]
            ])

            await message.reply("Select download option:", reply_markup=buttons)
            await fetching_msg.delete()

        except Exception as e:
            await fetching_msg.edit(f"⚠️ Error: {e}")

    @app.on_callback_query()
    async def button_click(client: Client, callback: CallbackQuery):
        data = callback.data
        option, download_url = data.split("|")
        downloading_msg = await callback.message.reply("⏳ Downloading... Please wait")

        try:
            # Download file
            local_filename = download_url.split("/")[-1]
            r = requests.get(download_url, stream=True)
            with open(local_filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

            # Send file
            if option == "audio":
                await client.send_audio(
                    chat_id=callback.message.chat.id,
                    audio=local_filename,
                    caption="Downloaded via SaveFrom.net",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]])
                )
            else:
                await client.send_video(
                    chat_id=callback.message.chat.id,
                    video=local_filename,
                    caption="Downloaded via SaveFrom.net",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]])
                )

            await downloading_msg.delete()
            if callback.message.reply_markup:
                await callback.message.delete()
            os.remove(local_filename)

        except Exception as e:
            await downloading_msg.edit(f"⚠️ Error while downloading: {e}")
