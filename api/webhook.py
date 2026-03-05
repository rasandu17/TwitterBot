"""
Vercel Serverless Function for Twitter Video Bot

This file is the main entry point for Vercel deployment.
It handles Telegram webhook requests in a serverless environment.
"""

from flask import Flask, request, jsonify
import asyncio
import re
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update, Bot
from downloader import is_valid_twitter_url, get_video_info, stream_video

# Get bot token from environment
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment variables")

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)


async def real_time_counter(chat_id, message_id, max_seconds=10):
    """Real-time elapsed counter while processing"""
    emojis = ["⏳", "⏱️", "⚡", "🔥", "💫", "✨"]
    start_time = asyncio.get_event_loop().time()
    counter = 0
    
    while counter < max_seconds * 2:
        try:
            elapsed = asyncio.get_event_loop().time() - start_time
            emoji = emojis[counter % len(emojis)]
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{emoji} Processing video...\n⏱️ Elapsed: {elapsed:.1f}s"
            )
        except Exception:
            # Ignore rate limits and other errors
            pass
        
        await asyncio.sleep(0.5)
        counter += 1


async def process_message(update_data):
    """Process incoming message asynchronously"""
    try:
        update = Update.de_json(update_data, bot)
        
        if not update.message or not update.message.text:
            return
        
        message_text = update.message.text
        chat_id = update.message.chat_id
        
        # Handle /start command
        if message_text.startswith('/start'):
            await bot.send_message(
                chat_id=chat_id,
                text=(
                    "👋 Welcome to Twitter Video Bot! ⚡\n\n"
                    "🚀 Ultra-fast video extraction\n"
                    "⏱️ Real-time countdown\n"
                    "📝 Tweet caption included\n\n"
                    "Just send me a Twitter/X video link!"
                )
            )
            return
        
        # Handle /help command
        if message_text.startswith('/help'):
            await bot.send_message(
                chat_id=chat_id,
                text=(
                    "ℹ️ Twitter Video Bot Help ⚡\n\n"
                    "📌 How to use:\n"
                    "1. Copy a Twitter/X video URL\n"
                    "2. Send it to me\n"
                    "3. Watch the countdown\n"
                    "4. Get your video with caption!\n\n"
                    "⚡ Deployed on Vercel serverless"
                )
            )
            return
        
        # Extract URLs
        url_pattern = r'https?://(?:www\.)?(?:twitter|x)\.com/\S+'
        urls = re.findall(url_pattern, message_text)
        
        if not urls:
            await bot.send_message(
                chat_id=chat_id,
                text="❌ No Twitter/X URL detected.\n\nSend a valid video link!"
            )
            return
        
        url = urls[0]
        
        if not is_valid_twitter_url(url):
            await bot.send_message(
                chat_id=chat_id,
                text="❌ Invalid URL.\n\nMust contain '/status/'"
            )
            return
        
        # Send status message
        status_msg = await bot.send_message(
            chat_id=chat_id,
            text="🔍 Extracting video... ⚡"
        )
        
        counter_task = None
        
        # Start real-time counter in background
        counter_task = asyncio.create_task(
            real_time_counter(chat_id, status_msg.message_id, 15)
        )
        
        # Extract video info (fast)
        video_info = get_video_info(url)
        
        # Cancel counter
        if counter_task and not counter_task.done():
            counter_task.cancel()
            try:
                await counter_task
            except asyncio.CancelledError:
                pass
        
        # Update status
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id,
                text="⚡ Streaming video..."
            )
        except:
            pass
        
        # Stream video from memory
        video_buffer = stream_video(video_info['url'])
        
        # Prepare caption with tweet text
        caption_text = "✅ Here's your video!"
        
        if video_info.get('caption'):
            tweet_text = video_info['caption']
            uploader = video_info.get('uploader', '')
            
            if uploader:
                caption_text = f"📱 @{uploader}\n\n💬 {tweet_text}\n\n✅ Powered by Vercel ⚡"
            else:
                caption_text = f"💬 {tweet_text}\n\n✅ Powered by Vercel ⚡"
            
            # Telegram caption limit
            if len(caption_text) > 1020:
                caption_text = caption_text[:1017] + "..."
        
        # Send video with caption
        video_buffer.name = f"{video_info['title']}.{video_info['ext']}"
        await bot.send_video(
            chat_id=chat_id,
            video=video_buffer,
            caption=caption_text,
            filename=f"{video_info['title']}.{video_info['ext']}"
        )
        
        # Delete status message
        try:
            await bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
        except:
            pass
        
    except Exception as e:
        print(f"Error processing message: {e}")
        
        # Cancel counter if still running
        if 'counter_task' in locals() and counter_task and not counter_task.done():
            counter_task.cancel()
            try:
                await counter_task
            except:
                pass
        
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=f"❌ Error: {str(e)}\n\nTry again or contact support."
            )
        except:
            pass


@app.route('/', methods=['GET'])
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'active',
        'bot': 'Twitter Video Bot',
        'version': '2.0 Vercel',
        'features': ['countdown', 'captions', 'ultra-fast', 'serverless']
    })


@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram webhooks"""
    try:
        update_data = request.get_json()
        
        # Process message asynchronously
        asyncio.run(process_message(update_data))
        
        return jsonify({'status': 'ok'})
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Vercel serverless function entry point
def handler(environ, start_response):
    """WSGI handler for Vercel"""
    return app(environ, start_response)


if __name__ == '__main__':
    app.run(debug=True)
