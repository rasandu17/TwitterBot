"""
Webhook handler for Vercel serverless deployment

This file handles incoming Telegram webhooks when deployed on Vercel.
It processes updates asynchronously without polling.

Deploy to Vercel:
1. Install Vercel CLI: npm i -g vercel
2. Set environment variable: vercel env add TELEGRAM_BOT_TOKEN
3. Deploy: vercel --prod
4. Set webhook: See VERCEL_DEPLOY.md
"""

from flask import Flask, request, jsonify
import asyncio
import re
from telegram import Update, Bot
from telegram.ext import ContextTypes
from config import BOT_TOKEN
from downloader import is_valid_twitter_url, get_video_info, stream_video

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
        
        # Handle commands
        if message_text.startswith('/start'):
            await bot.send_message(
                chat_id=chat_id,
                text=(
                    "👋 Welcome to Twitter Video Bot! ⚡\n\n"
                    "I can quickly extract and send videos from Twitter/X.\n"
                    "🚀 ULTRA-FAST with real-time countdown!\n\n"
                    "📝 Just send me a Twitter/X video link!"
                )
            )
            return
        
        if message_text.startswith('/help'):
            await bot.send_message(
                chat_id=chat_id,
                text=(
                    "ℹ️ Twitter Video Bot Help ⚡\n\n"
                    "📌 Send a Twitter/X video URL and get:\n"
                    "• The video file\n"
                    "• The tweet caption\n"
                    "• Real-time countdown\n\n"
                    "🚀 Deployed on Vercel for maximum speed!"
                )
            )
            return
        
        # Extract URLs
        url_pattern = r'https?://(?:www\.)?(?:twitter|x)\.com/\S+'
        urls = re.findall(url_pattern, message_text)
        
        if not urls:
            await bot.send_message(
                chat_id=chat_id,
                text="❌ No Twitter/X URL detected. Send a valid link!"
            )
            return
        
        url = urls[0]
        
        if not is_valid_twitter_url(url):
            await bot.send_message(
                chat_id=chat_id,
                text="❌ Invalid URL. Must contain '/status/'"
            )
            return
        
        # Send status message
        status_msg = await bot.send_message(
            chat_id=chat_id,
            text="🔍 Starting video extraction... ⚡"
        )
        
        counter_task = None
        
        # Start real-time counter
        counter_task = asyncio.create_task(
            real_time_counter(chat_id, status_msg.message_id, 15)
        )
        
        # Extract video info
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
                text="⚡ Streaming video... Almost there!"
            )
        except:
            pass
        
        # Stream video
        video_buffer = stream_video(video_info['url'])
        
        # Prepare caption with tweet text
        caption_text = "✅ Here's your video!"
        
        if video_info.get('caption'):
            tweet_text = video_info['caption']
            uploader = video_info.get('uploader', '')
            
            if uploader:
                caption_text = f"📱 @{uploader}\n\n{tweet_text}\n\n✅ Powered by Vercel"
            else:
                caption_text = f"{tweet_text}\n\n✅ Powered by Vercel"
            
            if len(caption_text) > 1020:
                caption_text = caption_text[:1017] + "..."
        
        # Send video
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
                text=f"❌ Error: {str(e)}"
            )
        except:
            pass


@app.route('/', methods=['GET'])
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'active',
        'bot': 'Twitter Video Bot',
        'version': '2.0',
        'features': ['countdown', 'captions', 'ultra-fast streaming']
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


# For Vercel serverless function
def handler(request):
    """Vercel serverless function handler"""
    with app.request_context(request.environ):
        return app.full_dispatch_request()


if __name__ == '__main__':
    # For local testing
    app.run(host='0.0.0.0', port=5000, debug=True)
