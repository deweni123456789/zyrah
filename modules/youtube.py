# modules/youtube.py
import os
import re
import asyncio
import tempfile
import requests
from functools import partial
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Optional fallback to yt_dlp if SaveFrom fails and cookies exist
try:
    from yt_dlp import YoutubeDL
    YTDLP_AVAILABLE = True
except Exception:
    YTDLP_AVAILABLE = False

# In-memory store for links per select message (key: (chat_id, message_id))
DOWNLOAD_STORE = {}

# SaveFrom worker endpoint (unofficial). Might change / rate-limit.
SAVEFROM_API = "https://worker.sf-api.com/savefrom.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0.0.0 Safari/537.36"
}

def parse_links_from_text(text):
    """Try to extract direct media URLs from arbitrary text (regex fallback)."""
    urls = []
    # match typical video/audio urls ending with common extensions or with signature parameters
    patterns = [
        r"https?://[^\s'\"<>]+\.mp4[^\s'\"<>]*",
        r"https?://[^\s'\"<>]+\.m4a[^\s'\"<>]*",
        r"https?://[^\s'\"<>]+\.webm[^\s'\"<>]*",
        r"https?://[^\s'\"<>]+/get_video\?[^'\"]+",
        r"https?://r[0-9]+--sn-[^'\"]+\.googlevideo\.com[^\s'\"<>]*"
    ]
    for pat in patterns:
        for m in re.findall(pat, text):
            if m not in urls:
                urls.append(m)
    return urls

def get_savefrom_links(youtube_url, timeout=12):
    """
    Query SaveFrom worker API and return list of dicts: [{'type':'video'/'audio','quality':..., 'link':...}, ...]
    Robust to non-JSON responses (tries regex fallback).
    """
    try:
        resp = requests.get(SAVEFROM_API, params={"url": youtube_url, "r": "user"}, headers=HEADERS, timeout=timeout)
    except Exception as e:
        # network error
        return {"ok": False, "error": f"Network error calling SaveFrom API: {e}", "links": []}

    if resp.status_code != 200:
        return {"ok": False, "error": f"SaveFrom API returned status {resp.status_code}", "links": []}

    text = resp.text.strip()
    if not text:
        return {"ok": False, "error": "SaveFrom returned empty response", "links": []}

    # Try JSON parse safely
    links = []
    try:
        data = resp.json()
        # many responses have "url" key as a list
        url_list = data.get("url") or data.get("links") or data.get("data") or []
        if isinstance(url_list, dict):
            # sometimes url is dict mapping keys -> lists
            # flatten
            for v in url_list.values():
                if isinstance(v, list):
                    for item in v:
                        link = item.get("url") or item.get("0") or item.get("link")
                        if link:
                            links.append({
                                "type": item.get("type") or ("audio" if "audio" in item.get("itag","") else "video"),
                                "quality": item.get("quality"),
                                "link": link
                            })
        elif isinstance(url_list, list):
            for item in url_list:
                # item might be string or dict
                if isinstance(item, dict):
                    link = item.get("url") or item.get("0") or item.get("link")
                    if not link:
                        # sometimes nested
                        for v in item.values():
                            if isinstance(v, str) and v.startswith("http"):
                                link = v
                                break
                    if link:
                        links.append({
                            "type": item.get("type") or ("audio" if "audio" in item.get("format","") else "video"),
                            "quality": item.get("quality", item.get("format")),
                            "link": link
                        })
                elif isinstance(item, str) and item.startswith("http"):
                    links.append({"type": "video", "quality": None, "link": item})
        # Deduplicate
        seen = set()
        filtered = []
        for it in links:
            if it["link"] not in seen:
                seen.add(it["link"])
                filtered.append(it)
        if filtered:
            return {"ok": True, "links": filtered}
        # else fallthrough to regex fallback
    except ValueError:
        # invalid JSON -> fallback to text parsing
        pass
    except Exception as e:
        # unexpected parsing error
        return {"ok": False, "error": f"Error parsing SaveFrom JSON: {e}", "links": []}

    # Regex fallback: try to find direct media URLs in HTML/JS
    found = parse_links_from_text(text)
    if found:
        fl = [{"type": "video", "quality": None, "link": u} for u in found]
        return {"ok": True, "links": fl}

    # No useful result
    return {"ok": False, "error": "SaveFrom returned no downloadable links", "links": []}

def download_stream_to_file(url, target_path, timeout=30):
    """Blocking download function (stream) — safe for large files."""
    headers = HEADERS.copy()
    # some hosts require Referer / Accept
    headers.setdefault("Referer", "https://www.youtube.com/")
    try:
        with requests.get(url, stream=True, headers=headers, timeout=timeout) as r:
            r.raise_for_status()
            total = r.headers.get("Content-Length")
            with open(target_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
        return {"ok": True, "path": target_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}

async def run_blocking(loop, func, *args):
    return await loop.run_in_executor(None, partial(func, *args))

def yt_dlp_download(url, outtmpl=None, cookiefile=None):
    """Blocking helper to download via yt-dlp. Returns local filepath or error."""
    if not YTDLP_AVAILABLE:
        return {"ok": False, "error": "yt_dlp not available in environment"}
    opts = {
        "format": "best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    if outtmpl:
        opts["outtmpl"] = outtmpl
    if cookiefile and os.path.exists(cookiefile):
        opts["cookiefile"] = cookiefile
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            # if audio conversion happened, adjust extension
            return {"ok": True, "path": path, "info": info}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def choose_best_link(links, prefer="video"):
    """Pick best link for type 'video' or 'audio'."""
    if not links:
        return None
    # prefer explicit type matches
    candidates = [l for l in links if prefer in (l.get("type") or "").lower()]
    if not candidates:
        candidates = links
    # try to pick best by quality (if present)
    # sort by quality string if numeric inside
    def qkey(it):
        q = it.get("quality") or ""
        nums = re.findall(r"\d+", str(q))
        return int(nums[0]) if nums else 0
    candidates.sort(key=qkey, reverse=True)
    return candidates[0]["link"] if candidates else None

#######################
# Pyrogram registration
#######################

def register_youtube(app: Client):
    @app.on_message(filters.private & filters.regex(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/\S+"))
    async def youtube_handler(client, message):
        url = message.text.strip()
        fetching = await message.reply("⏳ Fetching download links (SaveFrom) — please wait...")

        loop = asyncio.get_event_loop()
        result = await run_blocking(loop, get_savefrom_links, url)

        if not result.get("ok"):
            # SaveFrom failed — try fallback: use yt-dlp if cookies exist
            cookies_path = os.path.join(os.getcwd(), "cookies.txt")
            if YTDLP_AVAILABLE and os.path.exists(cookies_path):
                await fetching.edit("⚠️ SaveFrom failed — falling back to yt-dlp (using cookies). This may take a moment...")
                dl = await run_blocking(loop, yt_dlp_download, url, None, cookies_path)
                if dl.get("ok"):
                    path = dl.get("path")
                    # send file
                    try:
                        await client.send_document(chat_id=message.chat.id, document=path,
                                                   caption="Downloaded via yt-dlp fallback")
                    finally:
                        try: os.remove(path)
                        except: pass
                    await fetching.delete()
                    return
                else:
                    await fetching.edit(f"❌ yt-dlp fallback failed: {dl.get('error')}")
                    return
            else:
                # No cookies / yt-dlp fallback possible
                err_text = result.get("error") or "Unknown SaveFrom error"
                await fetching.edit(f"⚠️ SaveFrom failed: {err_text}\nNo yt-dlp/cookies fallback available.")
                return

        links = result.get("links", [])
        if not links:
            await fetching.edit("⚠️ No downloadable links found.")
            return

        # choose sample title (we don't have metadata reliably)
        title = url.split("v=")[-1].split("&")[0] if "v=" in url else url.split("/")[-1]
        requester = message.from_user.mention
        caption = f"🎬 {title}\nRequested by: {requester}"

        # store links by select message id
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📹 Download Video", callback_data="video")],
            [InlineKeyboardButton("🎵 Download Audio", callback_data="audio")],
            [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]
        ])

        select_msg = await message.reply("Select download option:", reply_markup=buttons)
        # store links under key (chat_id, message_id)
        DOWNLOAD_STORE[(select_msg.chat.id, select_msg.message_id)] = {
            "links": links,
            "title": title,
            "requester": requester
        }
        await fetching.delete()

    @app.on_callback_query()
    async def cb_handler(client: Client, callback: CallbackQuery):
        key = (callback.message.chat.id, callback.message.message_id)
        info = DOWNLOAD_STORE.get(key)
        if not info:
            await callback.answer("Links expired or not found. Please resend the YouTube link.", show_alert=True)
            try:
                await callback.message.delete()
            except: pass
            return

        option = callback.data  # 'video' or 'audio'
        links = info["links"]
        loop = asyncio.get_event_loop()
        await callback.answer("Starting download...")

        # pick best link
        link = choose_best_link(links, prefer=option)
        if not link:
            # fallback: if yt-dlp available and cookies, use it
            cookies_path = os.path.join(os.getcwd(), "cookies.txt")
            if YTDLP_AVAILABLE and os.path.exists(cookies_path):
                await callback.message.edit("⚠️ No direct link found — using yt-dlp fallback (cookies). This may take a while...")
                dl = await run_blocking(loop, yt_dlp_download, info.get("title"), None, cookies_path)  # pass URL? careful
                # above line incorrect since yt_dlp_download expects url; adjust:
                dl = await run_blocking(loop, yt_dlp_download, info.get("title") if False else callback.message.reply_to_message.text or "", None, cookies_path)
                if dl.get("ok"):
                    path = dl.get("path")
                    try:
                        if option == "audio":
                            await client.send_document(chat_id=callback.message.chat.id, document=path,
                                                       caption="Downloaded (yt-dlp fallback)")
                        else:
                            await client.send_document(chat_id=callback.message.chat.id, document=path,
                                                       caption="Downloaded (yt-dlp fallback)")
                    finally:
                        try: os.remove(path)
                        except: pass
                    # cleanup
                    try: del DOWNLOAD_STORE[key]
                    except: pass
                    try:
                        await callback.message.delete()
                    except: pass
                    return
                else:
                    await callback.message.edit(f"❌ yt-dlp fallback failed: {dl.get('error')}")
                    return
            await callback.message.edit("❌ No direct download link available for the selected type.")
            return

        # download the selected direct link in background
        tmpdir = tempfile.gettempdir()
        local_name = os.path.join(tmpdir, link.split("/")[-1].split("?")[0])
        # ensure unique
        base, ext = os.path.splitext(local_name)
        i = 0
        while os.path.exists(local_name):
            i += 1
            local_name = f"{base}_{i}{ext or '.mp4'}"

        await callback.message.edit("⏳ Downloading file — this can take some time for big videos...")
        res = await run_blocking(loop, download_stream_to_file, link, local_name)
        if not res.get("ok"):
            await callback.message.edit(f"⚠️ Download failed: {res.get('error')}")
            return

        # send file
        try:
            if option == "audio":
                # Telegram may prefer send_audio for audio files, but we can't be sure of mime
                await client.send_document(
                    chat_id=callback.message.chat.id,
                    document=local_name,
                    caption="Downloaded via SaveFrom",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]])
                )
            else:
                await client.send_document(
                    chat_id=callback.message.chat.id,
                    document=local_name,
                    caption="Downloaded via SaveFrom",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]])
                )
            # clean up
            try: os.remove(local_name)
            except: pass
            # remove stored links
            try: del DOWNLOAD_STORE[key]
            except: pass
            try:
                await callback.message.delete()
            except: pass
        except Exception as e:
            await callback.message.edit(f"⚠️ Error sending file: {e}")
            try:
                os.remove(local_name)
            except:
                pass
