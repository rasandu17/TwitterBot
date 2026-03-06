<p align="center">
  <img src="logo.png" alt="X Logo" width="100">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="telegram_logo.svg" alt="Telegram Logo" width="100">
</p>

# Twitter Video Bot

A Telegram bot that downloads videos from Twitter/X links and sends them directly to your chat.

## Features

- Fast video extraction from Twitter/X URLs
- Includes original tweet caption
- Real-time processing status
- Works in groups and private chats
- Deployed on Vercel (serverless)

## Setup

1. Get a bot token from [@BotFather](https://t.me/BotFather)
2. Clone this repo
3. Add `TELEGRAM_BOT_TOKEN` to your `.env` file
4. Deploy to Vercel or run locally

## Usage

Send any Twitter/X video link to the bot -- it will extract and send you the video.

## Tech Stack

- Python + Flask
- yt-dlp (video extraction)
- python-telegram-bot
- Vercel (serverless hosting)
