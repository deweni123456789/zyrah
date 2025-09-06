import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from instaloader import Instaloader, Post

# Regex to detect Instagram post URLs
INSTAGRAM_REGEX = re.compile(r"(https?://(www\.)?instagram\.com/p/\S+/)")

# Initialize Instaloader
L = Instaloader(download_videos=True, download_comments=False, save_metadata=False, download_geotags=False)

def get_instagram_metadata(url):
    try:
        post = Post.from_shortcode(L.context, url.split("/")[-2])
        metadata = {
            "caption": post.caption or "No caption",
            "uploader": post.owner_username,
            "likes": post.likes,
            "comments": post.comments,
            "url": url
        }
        return metadata
    except Exception as e:
        print("Metadata fetch error:", e)
        return None

def register_instagram(app: Client):
    @app.on_message(filters.private | filters.group)
    async def instagram_handler(client, message):
        if not message.text:
            return
        m = INSTAGRAM_REGEX.search(message.text)
        if not m:
            return

        url = m.group(0)
        metadata = get_instagram_metadata(url)

        buttons = [
            [InlineKeyboardButton("Download Video", callback_data=f"ig_video|{url}")],
            [InlineKeyboardButton("Download Audio", callback_data=f"ig_audio|{url}")],
            [InlineKeyboardButton("Developer @DEWENI2", url="https://t.me/deweni2")]
        ]
        await message.reply_text(
            text=f"Instagram post detected!\n\nUploader: {metadata['uploader'] if metadata else 'N/A'}\nCaption: {metadata['caption'] if metadata else 'N/A'}\nLikes: {metadata['likes'] if metadata else 'N/A'}\nComments: {metadata['comments'] if metadata else 'N/A'}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    @app.on_callback_query(filters.regex(r"^ig_"))
    async def ig_callback(client, callback_query):
        action, url = callback_query.data.split("|")
        await callback_query.answer("Downloading...")

        # Download using Instaloader
        try:
            post = Post.from_shortcode(L.context, url.split("/")[-2])
            filename = f"{post.shortcode}.mp4"

            if action == "ig_video":
                L.download_post(post, target=f"downloads/{post.shortcode}")
                file_path = f"downloads/{post.shortcode}/{post.shortcode}.mp4"
                await client.send_video(callback_query.from_user.id, file_path)
            elif action == "ig_audio":
                # Convert video to audio
                import moviepy.editor as mp
                L.download_post(post, target=f"downloads/{post.shortcode}")
                video_path = f"downloads/{post.shortcode}/{post.shortcode}.mp4"
                audio_path = f"downloads/{post.shortcode}/{post.shortcode}.mp3"
                clip = mp.VideoFileClip(video_path)
                clip.audio.write_audiofile(audio_path)
                await client.send_audio(callback_query.from_user.id, audio_path)

        except Exception as e:
            await callback_query.message.edit_text(f"❌ Error downloading: {e}")
