# 🚀 Deploy to Vercel - Complete Guide

Deploy your Twitter Video Bot to Vercel's serverless platform for **ultra-fast, free hosting**!

## Why Vercel?

✅ **Free tier** - Perfect for personal bots
✅ **Global CDN** - Fast worldwide
✅ **Auto-scaling** - Handles traffic spikes
✅ **Zero config** - Deploy in minutes
✅ **HTTPS included** - Secure by default

## Prerequisites

1. A Vercel account (free): https://vercel.com/signup
2. Your Telegram Bot Token from @BotFather
3. Git installed on your computer

## Step 1: Install Vercel CLI

### On Windows (PowerShell):
```powershell
npm install -g vercel
```

### On Mac/Linux:
```bash
npm install -g vercel
```

## Step 2: Login to Vercel

```bash
vercel login
```

Follow the prompts to authenticate with your Vercel account.

## Step 3: Prepare Your Project

Make sure you're in the project directory:

```bash
cd twitter_video_bot
```

## Step 4: Set Environment Variables

You need to add your bot token to Vercel:

```bash
vercel env add TELEGRAM_BOT_TOKEN
```

When prompted:
- **Environment**: Select "Production"
- **Value**: Paste your bot token from BotFather

Example: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

## Step 5: Deploy to Vercel

Deploy your bot:

```bash
vercel --prod
```

This will:
- Upload your code
- Build the serverless functions
- Deploy to production
- Give you a URL like: `https://your-project.vercel.app`

**Copy this URL!** You'll need it in the next step.

## Step 6: Set Telegram Webhook

Once deployed, you need to tell Telegram where to send updates.

### Option A: Using curl (Recommended)

Replace `YOUR_BOT_TOKEN` and `YOUR_VERCEL_URL`:

```bash
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook?url=YOUR_VERCEL_URL/webhook"
```

**Example:**
```bash
curl -X POST "https://api.telegram.org/bot1234567890:ABCdef/setWebhook?url=https://my-bot.vercel.app/webhook"
```

### Option B: Using Python

Create a file called `set_webhook.py`:

```python
import requests
import os

BOT_TOKEN = "YOUR_BOT_TOKEN"  # Replace with your token
VERCEL_URL = "YOUR_VERCEL_URL"  # Replace with your Vercel URL

url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
data = {"url": f"{VERCEL_URL}/webhook"}

response = requests.post(url, json=data)
print(response.json())
```

Run it:
```bash
python set_webhook.py
```

### Option C: Using Browser

Open this URL in your browser (replace the values):

```
https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook?url=YOUR_VERCEL_URL/webhook
```

You should see:
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

## Step 7: Test Your Bot

1. Open Telegram
2. Send `/start` to your bot
3. Send a Twitter/X video URL
4. Watch the countdown and receive your video! ⚡

## Verify Deployment

Check if your bot is running:

1. Visit your Vercel URL: `https://your-project.vercel.app`
2. You should see: `{"status": "active", "bot": "Twitter Video Bot", ...}`

Check webhook status:
```bash
curl https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo
```

## Common Issues & Solutions

### Issue: Bot doesn't respond

**Solution:**
1. Check webhook is set correctly:
   ```bash
   curl https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo
   ```
2. Verify environment variable is set in Vercel dashboard
3. Check Vercel function logs: `vercel logs`

### Issue: "TELEGRAM_BOT_TOKEN not set"

**Solution:**
Add the environment variable:
```bash
vercel env add TELEGRAM_BOT_TOKEN
```
Then redeploy:
```bash
vercel --prod
```

### Issue: Timeout errors

**Solution:**
Vercel free tier has 10-second timeout. Large videos may fail.
Upgrade to Pro tier for 60-second timeout if needed.

### Issue: Cold starts (first request is slow)

**Solution:**
This is normal for serverless. After the first request, subsequent ones are fast.
Consider upgrading to Vercel Pro to minimize cold starts.

## Update Your Bot

When you make changes:

1. Commit your changes:
   ```bash
   git add .
   git commit -m "Update bot features"
   ```

2. Redeploy:
   ```bash
   vercel --prod
   ```

Vercel will automatically update your deployment!

## Monitoring & Logs

View real-time logs:
```bash
vercel logs --follow
```

View logs in Vercel Dashboard:
1. Go to https://vercel.com/dashboard
2. Select your project
3. Click "Logs" tab

## Free Tier Limits

Vercel free tier includes:
- ✅ 100GB bandwidth/month
- ✅ 100 hours serverless function execution/month
- ✅ Unlimited requests
- ✅ Automatic HTTPS

This is **more than enough** for personal bot usage!

## Custom Domain (Optional)

Want a custom domain like `bot.yourdomain.com`?

1. Go to your project dashboard on Vercel
2. Click "Settings" → "Domains"
3. Add your custom domain
4. Update webhook URL:
   ```bash
   curl -X POST "https://api.telegram.org/botYOUR_TOKEN/setWebhook?url=https://bot.yourdomain.com/webhook"
   ```

## Pause/Delete Webhook (Switch back to local)

To run locally again:

1. Delete webhook:
   ```bash
   curl -X POST "https://api.telegram.org/botYOUR_TOKEN/deleteWebhook"
   ```

2. Run locally:
   ```bash
   python bot.py
   ```

## Environment Variables in Vercel Dashboard

Alternatively, set environment variables via web interface:

1. Go to https://vercel.com/dashboard
2. Select your project
3. Settings → Environment Variables
4. Add `TELEGRAM_BOT_TOKEN` with your token value
5. Redeploy

## Production Checklist

Before going live:

- [ ] Bot token is set in Vercel environment variables
- [ ] Code is deployed to production (`vercel --prod`)
- [ ] Webhook is set correctly
- [ ] Test all commands (/start, /help)
- [ ] Test with a real Twitter video URL
- [ ] Verify countdown works
- [ ] Verify caption extraction works
- [ ] Check Vercel logs for errors

## Performance Tips

1. **Optimize yt-dlp**: Already optimized with `skip_download: True`
2. **Use CDN**: Vercel automatically uses global CDN
3. **Monitor coldstarts**: First request may be slow (2-3 seconds)
4. **Upgrade if needed**: Vercel Pro removes many limits

## Cost Estimate

**Free tier usage example:**
- 1000 videos/month
- Average 5MB per video
- = 5GB bandwidth used
- = ~2 hours function execution

**Result:** Still well within free limits! 🎉

## Support & Help

- **Vercel Docs**: https://vercel.com/docs
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **Project Issues**: Check GitHub repo

## Next Steps

Once deployed:
1. Share your bot with friends!
2. Monitor usage in Vercel dashboard
3. Check out advanced features (custom domains, analytics)

---

**Congratulations! Your bot is now hosted on Vercel!** 🎉⚡

Your bot runs on-demand with zero maintenance required!
