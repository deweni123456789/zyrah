import re, os, shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import instaloader
from moviepy.editor import VideoFileClip

# Regex to detect Instagram post URLs
INSTAGRAM_REGEX = re.compile(r"(https?://(www\.)?instagram\.com/p/\S+/)")

# Initialize Instaloader
L = instaloader.Instaloader(
    download_videos=True,
    download_comments=False,
    save_metadata=False,
    download_geotags=False
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def register_instagram(app: Client):

    @app.on_message(filters.private | filters.group)
    async def instagram_handler(client, message):
        if not message.text:
            return
        m = INSTAGRAM_REGEX.search(message.text)
        if not m:
            return

        url = m.group(0)
        shortcode = url.split("/")[-2]

        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode)
        except Exception as e:
            await message.reply_text(f"❌ Failed to fetch Instagram post: {e}")
            return

        # Metadata
        metadata_text = f"Instagram post detected!\n\nUploader: {post.owner_username}\nCaption: {post.caption or 'No caption'}\nLikes: {post.likes}\nComments: {post.comments}"

        # Buttons
        buttons = [
            [InlineKeyboardButton("Download Video", callback_data=f"ig_video|{shortcode}")],
            [InlineKeyboardButton("Download Audio", callback_data=f"ig_audio|{shortcode}")],
            [InlineKeyboardButton("Developer @DEWENI2", url="https://t.me/deweni2")]
        ]

        await message.reply_text(text=metadata_text, reply_markup=InlineKeyboardMarkup(buttons))

    @app.on_callback_query(filters.regex(r"^ig_"))
    async def ig_callback(client, callback_query):
        action, shortcode = callback_query.data.split("|")
        await callback_query.answer("Downloading...")

        post_dir = os.path.join(DOWNLOAD_DIR, shortcode)
        os.makedirs(post_dir, exist_ok=True)

        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            # Download video once
            L.download_post(post, target=post_dir)
            video_files = [f for f in os.listdir(post_dir) if f.endswith(".mp4")]
            if not video_files:
                await callback_query.message.edit_text("❌ No video found in this post.")
                return
            video_path = os.path.join(post_dir, video_files[0])

            if action == "ig_video":
                await client.send_video(callback_query.message.chat.id, video_path)
            elif action == "ig_audio":
                audio_path = os.path.join(post_dir, f"{shortcode}.mp3")
                clip = VideoFileClip(video_path)
                clip.audio.write_audiofile(audio_path)
                clip.close()
                await client.send_audio(callback_query.message.chat.id, audio_path)

            # Clean up
            shutil.rmtree(post_dir, ignore_errors=True)

        except Exception as e:
            await callback_query.message.edit_text(f"❌ Error downloading: {e}")
