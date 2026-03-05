# 🚀 Quick Start Guide

Get your Twitter Video Bot running in **5 minutes**! Choose your preferred method:

## Method 1: Run Locally (Easiest) ⚡

Perfect for testing and personal use.

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Bot Token
Edit `.env` file:
```
TELEGRAM_BOT_TOKEN=your_token_from_botfather
```

### Step 3: Run Bot
```bash
python bot.py
```

**Done!** Your bot is now running locally. ✅

---

## Method 2: Deploy to Vercel (Production) ☁️

Perfect for 24/7 hosting with zero maintenance.

### Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

### Step 2: Login
```bash
vercel login
```

### Step 3: Set Token
```bash
vercel env add TELEGRAM_BOT_TOKEN
# Paste your bot token when prompted
```

### Step 4: Deploy
```bash
vercel --prod
```

### Step 5: Set Webhook
```bash
python set_webhook.py --set https://your-project.vercel.app/webhook
```

**Done!** Your bot is now live 24/7 on Vercel! ✅

See [VERCEL_DEPLOY.md](VERCEL_DEPLOY.md) for detailed instructions.

---

## Testing Your Bot

1. Open Telegram
2. Search for your bot
3. Send `/start`
4. Send a Twitter video URL like:
   ```
   https://twitter.com/username/status/123456789
   ```
5. Watch the countdown! ⏱️
6. Receive your video with caption! 📝

---

## Common Issues

### "Bot token not found"
**Fix:** Make sure `.env` file exists and contains your token.

### Bot doesn't respond (local)
**Fix:** Make sure bot is running: `python bot.py`

### Bot doesn't respond (Vercel)
**Fix:** Check webhook is set:
```bash
python set_webhook.py --info
```

### "No video found"
**Fix:** Tweet must contain a video (not just an image or GIF).

---

## What's Next?

- ✅ Invite friends to try your bot
- ✅ Monitor usage (if deployed on Vercel)
- ✅ Check out advanced features
- ✅ Customize the messages in `bot.py`

---

## Support

- 📖 Full docs: [README.md](README.md)
- ☁️ Vercel guide: [VERCEL_DEPLOY.md](VERCEL_DEPLOY.md)
- 🎉 What's new: [CHANGELOG.md](CHANGELOG.md)

**Enjoy your ultra-fast Twitter video bot!** ⚡🎉
