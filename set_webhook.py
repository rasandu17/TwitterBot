"""
Helper script to set/delete Telegram webhooks

This script helps you easily set up or remove webhooks for your bot.

Usage:
1. Set webhook: python set_webhook.py --set https://your-vercel-url.vercel.app/webhook
2. Delete webhook: python set_webhook.py --delete
3. Check webhook: python set_webhook.py --info
"""

import requests
import argparse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env file")
    print("Please set your bot token in the .env file first.")
    exit(1)

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def set_webhook(webhook_url):
    """Set webhook URL for the bot"""
    print(f"🔧 Setting webhook to: {webhook_url}")
    
    url = f"{API_URL}/setWebhook"
    data = {"url": webhook_url}
    
    try:
        response = requests.post(url, json=data)
        result = response.json()
        
        if result.get('ok'):
            print("✅ Webhook set successfully!")
            print(f"   URL: {webhook_url}")
            return True
        else:
            print(f"❌ Failed to set webhook: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def delete_webhook():
    """Delete webhook (switch back to polling mode)"""
    print("🗑️ Deleting webhook...")
    
    url = f"{API_URL}/deleteWebhook"
    
    try:
        response = requests.post(url)
        result = response.json()
        
        if result.get('ok'):
            print("✅ Webhook deleted successfully!")
            print("   Bot is now in polling mode (for local use)")
            return True
        else:
            print(f"❌ Failed to delete webhook: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def get_webhook_info():
    """Get current webhook information"""
    print("ℹ️ Getting webhook information...")
    
    url = f"{API_URL}/getWebhookInfo"
    
    try:
        response = requests.get(url)
        result = response.json()
        
        if result.get('ok'):
            info = result.get('result', {})
            
            print("\n📊 Webhook Status:")
            print(f"   URL: {info.get('url', 'Not set (polling mode)')}")
            print(f"   Pending updates: {info.get('pending_update_count', 0)}")
            
            if info.get('last_error_date'):
                print(f"   ⚠️ Last error: {info.get('last_error_message')}")
            else:
                print("   ✅ No errors")
            
            return True
        else:
            print(f"❌ Failed to get info: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Manage Telegram bot webhooks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set webhook for Vercel deployment
  python set_webhook.py --set https://your-bot.vercel.app/webhook
  
  # Check current webhook status
  python set_webhook.py --info
  
  # Delete webhook (switch to local polling)
  python set_webhook.py --delete
        """
    )
    
    parser.add_argument('--set', metavar='URL', help='Set webhook URL')
    parser.add_argument('--delete', action='store_true', help='Delete webhook')
    parser.add_argument('--info', action='store_true', help='Get webhook info')
    
    args = parser.parse_args()
    
    print("🤖 Twitter Video Bot - Webhook Manager\n")
    
    if args.set:
        if not args.set.startswith('https://'):
            print("❌ Error: Webhook URL must use HTTPS")
            print("   Example: https://your-bot.vercel.app/webhook")
            exit(1)
        set_webhook(args.set)
    elif args.delete:
        delete_webhook()
    elif args.info:
        get_webhook_info()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
