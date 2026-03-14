"""
Twitter Video Bot + Viral Post Generator

Features:
- Download Twitter/X videos (send a tweet URL)
- Generate viral fact posts (send a photo + news text as caption)

Post creation workflow:
  1. Send a photo with the news text as the caption
  2. Bot uses Groq AI to create a punchy viral caption
  3. Bot sends back the finished post image

Optional: Send TWO photos in one message (album) — the second
photo will appear as a circular inset in the top-right corner.
"""

import re
import io
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from config import BOT_TOKEN
from downloader import is_valid_twitter_url, get_video_info, stream_video
from post_generator import create_post_from_photo
from groq_post import generate_viral_content


# ── /start ─────────────────────────────────────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "📹 *Twitter/X Video Downloader*\n"
        "Just send a tweet URL and I'll send back the video.\n\n"
        "🖼️ *Viral Post Generator*\n"
        "Send a *photo* with the news text as the *caption*.\n"
        "I'll create a viral styled post image for you!\n\n"
        "💡 Tip: Send *two photos* in one album — the second\n"
        "will appear as a circular inset in the top-right corner.\n\n"
        "Use /help for details.",
        parse_mode="Markdown"
    )


# ── /help ──────────────────────────────────────────────────────────────────────
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *How to use this bot*\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📹 *Download Twitter/X Videos*\n"
        "Send any tweet URL:\n"
        "`https://x.com/user/status/123...`\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "🖼️ *Create Viral Post Images*\n"
        "1. Attach a photo (your background image)\n"
        "2. Write the news/fact as the *caption*\n"
        "3. Send it — I'll generate the styled post!\n\n"
        "Example caption:\n"
        "_In Haiti families eat mud cookies to survive hunger_\n\n"
        "📌 *Two-photo mode:*\n"
        "Send 2 photos in one album — the 2nd appears as\n"
        "a circular inset image in the top-right corner.\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "⚙️ Make sure GROQ\\_API\\_KEY is set in your .env file.\n"
        "Get a free key at: https://console.groq.com",
        parse_mode="Markdown"
    )


# ── Album (MediaGroup) handler ─────────────────────────────────────────────────
# We collect messages in the same media_group_id and process after a short delay.
MEDIA_GROUPS: dict[str, dict] = {}   # group_id → {photos: [], caption: str, task: Task}


async def _process_media_group(group_id: str, update: Update,
                                context: ContextTypes.DEFAULT_TYPE):
    """Called after a short delay once all album photos have arrived."""
    await asyncio.sleep(1.5)   # wait for all album parts to arrive

    group = MEDIA_GROUPS.pop(group_id, None)
    if not group:
        return

    photos = group.get("photos", [])
    caption = group.get("caption", "")
    message = group.get("message")

    if not caption:
        await message.reply_text(
            "❌ Please add the news text as the *caption* of your photo!\n\n"
            "Example: attach a photo and write the news as caption.",
            parse_mode="Markdown"
        )
        return

    await _generate_post(message, context, photos, caption)


async def handle_album_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect photos from a media group (album)."""
    msg = update.message
    group_id = msg.media_group_id

    # Get the best quality photo
    photo_file = await msg.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()

    if group_id not in MEDIA_GROUPS:
        MEDIA_GROUPS[group_id] = {
            "photos": [],
            "caption": msg.caption or "",
            "message": msg,
            "task": None,
        }

    MEDIA_GROUPS[group_id]["photos"].append(bytes(photo_bytes))

    # Update caption if this message has it
    if msg.caption:
        MEDIA_GROUPS[group_id]["caption"] = msg.caption

    # Cancel previous timer and restart (wait for all album photos)
    if MEDIA_GROUPS[group_id]["task"]:
        MEDIA_GROUPS[group_id]["task"].cancel()

    task = asyncio.create_task(
        _process_media_group(group_id, update, context)
    )
    MEDIA_GROUPS[group_id]["task"] = task


# ── Single photo handler ───────────────────────────────────────────────────────
async def handle_single_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle a single photo sent with a caption."""
    msg = update.message

    # Ignore if it's part of an album (handled separately)
    if msg.media_group_id:
        await handle_album_photo(update, context)
        return

    caption = msg.caption or ""
    if not caption:
        await msg.reply_text(
            "❌ Please send your photo *with a caption* — "
            "write the news/fact text as the caption!\n\n"
            "Example: attach a photo and type the news as caption.",
            parse_mode="Markdown"
        )
        return

    photo_file = await msg.photo[-1].get_file()
    photo_bytes = bytes(await photo_file.download_as_bytearray())

    await _generate_post(msg, context, [photo_bytes], caption)


# ── Core post generation ───────────────────────────────────────────────────────
async def _generate_post(message, context: ContextTypes.DEFAULT_TYPE,
                          photos: list[bytes], news_text: str):
    """Generate and send the viral post image + ready-to-post description."""
    status = await message.reply_text("✍️ Generating content with Groq AI...")

    try:
        # Step 1: Groq generates both the styled caption and post description
        content = generate_viral_content(news_text)
        styled_caption = content["caption"]
        description    = content["description"]

        await status.edit_text("🎨 Composing your post image...")

        # Step 2: Compose the image
        bg_bytes    = photos[0]
        inset_bytes = photos[1] if len(photos) >= 2 else None

        img_buf = create_post_from_photo(
            bg_bytes=bg_bytes,
            styled_text=styled_caption,
            inset_bytes=inset_bytes,
        )

        # Step 3: Send the image
        await message.reply_photo(photo=img_buf)
        await status.delete()

        # Step 4: Send the ready-to-post description as a separate message
        await message.reply_text(
            f"{description}",
            parse_mode=None   # plain text, ready to copy-paste
        )

    except ValueError as e:
        await status.edit_text(f"⚠️ Configuration error:\n\n{e}")
    except Exception as e:
        await status.edit_text(
            f"❌ Something went wrong:\n\n{str(e)[:300]}"
        )


# ── Twitter/X URL handler ──────────────────────────────────────────────────────
async def real_time_counter(message, max_seconds: int = 15):
    emojis = ["⏳", "⏱️", "⚡", "🔥", "💫", "✨"]
    start = asyncio.get_event_loop().time()
    i = 0
    while i < max_seconds * 2:
        try:
            elapsed = asyncio.get_event_loop().time() - start
            await message.edit_text(
                f"{emojis[i % len(emojis)]} Processing video...\n"
                f"⏱️ Elapsed: {elapsed:.1f}s"
            )
        except Exception:
            pass
        await asyncio.sleep(0.5)
        i += 1


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages — look for Twitter/X URLs."""
    text = update.message.text or ""

    url_pattern = r'https?://(?:www\.)?(?:twitter|x)\.com/\S+'
    urls = re.findall(url_pattern, text)

    if not urls:
        await update.message.reply_text(
            "ℹ️ To create a viral post, send a *photo* with the news as caption.\n"
            "To download a video, send a Twitter/X URL.\n"
            "Use /help for instructions.",
            parse_mode="Markdown"
        )
        return

    url = urls[0]
    if not is_valid_twitter_url(url):
        await update.message.reply_text(
            "❌ Invalid Twitter/X URL. It must contain `/status/`."
        )
        return

    status = await update.message.reply_text("🔍 Starting video extraction... ⚡")
    counter_task = None

    try:
        counter_task = asyncio.create_task(real_time_counter(status, 15))
        video_info = get_video_info(url)
        video_buffer = stream_video(video_info["url"])

        if counter_task and not counter_task.done():
            counter_task.cancel()
            try:
                await counter_task
            except Exception:
                pass

        caption_text = "✅ Here's your video!"
        if video_info.get("caption"):
            tweet = video_info["caption"]
            upl = video_info.get("uploader", "")
            caption_text = (
                f"📱 @{upl}\n\n{tweet}\n\n✅ Downloaded by Twitter Video Bot"
                if upl else f"{tweet}\n\n✅ Downloaded by Twitter Video Bot"
            )
            if len(caption_text) > 1020:
                caption_text = caption_text[:1017] + "..."

        video_buffer.name = f"{video_info['title']}.{video_info['ext']}"
        await update.message.reply_video(
            video=video_buffer,
            caption=caption_text,
            filename=f"{video_info['title']}.{video_info['ext']}",
        )
        try:
            await status.delete()
        except Exception:
            pass

    except Exception as e:
        if counter_task and not counter_task.done():
            counter_task.cancel()
            try:
                await counter_task
            except Exception:
                pass
        try:
            await status.edit_text(
                f"❌ Unable to process video.\n\nError: {str(e)}"
            )
        except Exception:
            await update.message.reply_text(
                f"❌ Unable to process video.\n\nError: {str(e)}"
            )


# ── Error handler ──────────────────────────────────────────────────────────────
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[ERROR] Update {update} caused: {context.error}")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("🤖 Starting bot...")

    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))

    # Photos (single or album)
    app.add_handler(MessageHandler(filters.PHOTO, handle_single_photo))

    # Text / URLs
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Errors
    app.add_error_handler(error_handler)

    print("✅ Bot is running! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    import asyncio
    # Fix for Python 3.12 + Windows: use the Selector event loop
    # (ProactorEventLoop causes 'ExtBot not initialized' errors with python-telegram-bot)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
