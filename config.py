"""
Configuration file for the Twitter Video Bot

Instructions:
1. Create a Telegram bot using BotFather:
   - Open Telegram and search for @BotFather
   - Send /newbot command
   - Follow the instructions to set your bot name and username
   - Copy the bot token provided by BotFather

2. Set the bot token:
   Option A: Create a .env file in the project root with:
   TELEGRAM_BOT_TOKEN=your_token_here
   
   Option B: Set as an environment variable:
   - Windows CMD: set TELEGRAM_BOT_TOKEN=your_token_here
   - Windows PowerShell: $env:TELEGRAM_BOT_TOKEN="your_token_here"
   - Linux/Mac: export TELEGRAM_BOT_TOKEN=your_token_here
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the bot token from environment variable
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Validate that token is set
if not BOT_TOKEN:
    raise ValueError(
        "Bot token not found! Please set the TELEGRAM_BOT_TOKEN environment variable.\n"
        "Example: export TELEGRAM_BOT_TOKEN='your_token_here'"
    )

# Directory to store temporary downloads
DOWNLOADS_DIR = 'downloads'

# Maximum file size for Telegram (50MB in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024
