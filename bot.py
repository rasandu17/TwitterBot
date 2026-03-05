"""
Twitter Video Bot - Ultra-Fast Version with Countdown & Caption Extraction

This bot extracts and streams videos from Twitter/X with real-time countdown.
Optimized for Vercel serverless deployment!

Features:
- Real-time countdown during processing
- Tweet caption extraction
- Ultra-fast streaming (no local storage)
- Webhook support for Vercel deployment

Installation Instructions:
1. Install Python 3.7 or higher
2. Install dependencies: pip install -r requirements.txt
3. Create a bot using Telegram BotFather (@BotFather)
4. Set your bot token in .env file
5. Run locally: python bot.py
6. Deploy to Vercel: See VERCEL_DEPLOY.md

How to use:
- Send /start to get a welcome message
- Send /help to see instructions
- Send any Twitter/X video URL to get the video with countdown! ⚡
"""

import re
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from config import BOT_TOKEN
from downloader import is_valid_twitter_url, get_video_info, stream_video


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for the /start command.
    Sends a welcome message to the user.
    """
    welcome_message = (
        "👋 Welcome to Twitter Video Bot! ⚡\n\n"
        "🎯 New Features:\n"
        "⏱️ Real-time elapsed timer\n"
        "📝 Tweet caption extraction\n"
        "🚀 Ultra-fast streaming (3-5 seconds)\n\n"
        "📝 How to use:\n"
        "Just send me a Twitter or X video link like:\n"
        "• https://twitter.com/username/status/123456789\n"
        "• https://x.com/username/status/123456789\n\n"
        "Watch the real-time timer and get your video with the original tweet text!\n\n"
        "Use /help for more information."
    )
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for the /help command.
    Provides instructions on how to use the bot.
    """
    help_message = (
        "ℹ️ Twitter Video Bot Help ⚡\n\n"
        "📌 How to use this bot:\n"
        "1. Find a video on Twitter or X\n"
        "2. Copy the tweet URL (must contain /status/)\n"
        "3. Send the URL to me\n"
        "4. Watch the real-time timer ⏱️\n"
        "5. Get your video with the original tweet caption! 📝\n\n"
        "✅ Supported URL formats:\n"
        "• https://twitter.com/user/status/123...\n"
        "• https://x.com/user/status/123...\n\n"
        "⚡ What you get:\n"
        "• High quality video file\n"
        "• Original tweet text as caption\n"
        "• Tweet author's username\n"
        "• Real-time elapsed timer feedback\n"
        "• Delivery in 3-5 seconds\n\n"
        "🚀 Speed Features:\n"
        "• Direct streaming - NO local downloads\n"
        "• 5-10x faster than traditional methods\n"
        "• Perfect for serverless hosting\n"
        "• No files stored on server\n\n"
        "⚠️ Note:\n"
        "• Only video tweets are supported\n"
        "• Files larger than 50MB may fail (Telegram limit)\n"
        "• Tweet must be public\n\n"
        "❓ Need help? Contact the bot developer."
    )
    await update.message.reply_text(help_message)


async def real_time_counter(message, max_seconds=10):
    """
    Shows a real-time elapsed counter while processing.
    Updates every 0.5 seconds to show actual processing time.
    
    Args:
        message: The message object to edit
        max_seconds: Maximum seconds to count (safety limit)
    """
    emojis = ["⏳", "⏱️", "⚡", "🔥", "💫", "✨"]
    start_time = asyncio.get_event_loop().time()
    counter = 0
    
    while counter < max_seconds * 2:  # *2 because we update every 0.5s
        try:
            elapsed = asyncio.get_event_loop().time() - start_time
            emoji = emojis[counter % len(emojis)]
            
            # Show elapsed time with one decimal place
            await message.edit_text(
                f"{emoji} Processing video...\n"
                f"⏱️ Elapsed: {elapsed:.1f}s"
            )
        except Exception:
            # Ignore errors from message editing (rate limits, etc.)
            pass
        
        await asyncio.sleep(0.5)
        counter += 1


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for regular text messages.
    Detects Twitter/X URLs, shows countdown, extracts captions, and streams videos.
    """
    message_text = update.message.text
    
    # Extract URLs from the message
    url_pattern = r'https?://(?:www\.)?(?:twitter|x)\.com/\S+'
    urls = re.findall(url_pattern, message_text)
    
    if not urls:
        # No URLs found in the message
        await update.message.reply_text(
            "❌ No Twitter/X URL detected.\n\n"
            "Please send a valid Twitter or X video link.\n"
            "Use /help for more information."
        )
        return
    
    # Process the first URL found
    url = urls[0]
    
    # Validate the URL
    if not is_valid_twitter_url(url):
        await update.message.reply_text(
            "❌ Invalid Twitter/X URL.\n\n"
            "Please send a URL containing '/status/' like:\n"
            "https://twitter.com/username/status/123456789"
        )
        return
    
    # Send initial status message
    status_message = await update.message.reply_text("🔍 Starting video extraction... ⚡")
    
    # Variable to track if we had an error
    counter_task = None
    
    try:
        # Start real-time counter in background while extracting info
        counter_task = asyncio.create_task(real_time_counter(status_message, 15))
        
        # Extract video info (fast - no download yet)
        video_info = get_video_info(url)
        
        # Stream video directly into memory (no disk storage)
        # Counter keeps running to show elapsed time
        video_buffer = stream_video(video_info['url'])
        
        # Cancel counter now that we have the video
        if counter_task and not counter_task.done():
            counter_task.cancel()
            try:
                await counter_task
            except:
                pass  # Ignore any cancellation errors
        
        # Prepare caption with tweet text
        caption_text = "✅ Here's your video!"
        
        if video_info.get('caption'):
            # Include the actual tweet text
            tweet_text = video_info['caption']
            uploader = video_info.get('uploader', '')
            
            # Format caption nicely
            if uploader:
                caption_text = f"📱 @{uploader}\n\n{tweet_text}\n\n✅ Downloaded by Twitter Video Bot"
            else:
                caption_text = f"{tweet_text}\n\n✅ Downloaded by Twitter Video Bot"
            
            # Telegram caption limit is 1024 characters
            if len(caption_text) > 1020:
                caption_text = caption_text[:1017] + "..."
        
        # Send the video directly from memory with caption
        video_buffer.name = f"{video_info['title']}.{video_info['ext']}"
        await update.message.reply_video(
            video=video_buffer,
            caption=caption_text,
            filename=f"{video_info['title']}.{video_info['ext']}"
        )
        
        # Delete the status message (ignore if already deleted)
        try:
            await status_message.delete()
        except:
            pass
        
        # Success! Don't show any error message
        return
        
    except Exception as e:
        # Cancel counter if still running
        if counter_task and not counter_task.done():
            counter_task.cancel()
            try:
                await counter_task
            except:
                pass
        
        # Handle real errors only
        error_message = (
            "❌ Unable to process video.\n\n"
            "Possible reasons:\n"
            "• The tweet doesn't contain a video\n"
            "• The video is unavailable or private\n"
            "• The link is invalid\n"
            "• Network or server error\n\n"
            f"Error details: {str(e)}"
        )
        try:
            await status_message.edit_text(error_message)
        except:
            # If status message was already deleted, send new error message
            try:
                await update.message.reply_text(error_message)
            except:
                pass


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for errors that occur during bot operation.
    """
    print(f"Update {update} caused error {context.error}")


def main():
    """
    Main function to start the bot.
    """
    print("🤖 Starting Twitter Video Bot...")
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Register message handler for text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
