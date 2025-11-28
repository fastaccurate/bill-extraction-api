# Quick Start Guide - Deploy in 5 Minutes

## The Goal

You're about to deploy a **free, production-ready bill extraction API** to get a public webhook URL.

**Final endpoint:** `https://bill-extraction-api-XXXX.onrender.com/extract-bill-data`

---

## Prerequisites

- GitHub account (free): https://github.com/signup
- Render account (free): https://render.com/signup

**Time needed:** 5-10 minutes  
**Cost:** $0

---

## Step 1: Organize Files

```bash
mkdir bill-extraction-api
cd bill-extraction-api

# Copy all files into this folder:
# - main.py
# - config.py
# - schemas.py
# - requirements.txt
# - Dockerfile
# - .env.example
# - README.md
# - All service files

# Create services subfolder
mkdir services
mv services_*.py services/
```

Create `services/__init__.py`:
```bash
touch services/__init__.py
```

---

## Step 2: Create .git Repository

```bash
git init
git add .
git commit -m "Initial commit: Bill extraction API"
```

---

## Step 3: Push to GitHub

1. Go to https://github.com/new
2. Create new repository: `bill-extraction-api`
3. Choose **Public** (so Render can access)
4. Don't initialize with README

Then run:

```bash
git remote add origin https://github.com/YOUR_USERNAME/bill-extraction-api.git
git branch -M main
git push -u origin main
```

**Done!** Your code is now on GitHub.

---

## Step 4: Deploy on Render

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Click **Connect Repository**
4. Search for `bill-extraction-api`
5. Click **Connect**
6. Fill in details:
   - **Name:** `bill-extraction-api`
   - **Region:** Choose closest to you
   - **Branch:** `main`
   - **Runtime:** `Docker`
   - **Build Command:** (leave empty)
   - **Start Command:** (leave empty)

7. Scroll down and click **Create Web Service**

**Render starts building immediately** (~5 minutes)

---

## Step 5: Get Your Webhook URL

1. Wait for build to complete (you'll see logs scrolling)
2. Once live, you'll see: ✅ **Service is Live**
3. Look at the top - you'll see:
   ```
   https://bill-extraction-api-XXXX.onrender.com
   ```

4. Your webhook endpoint is:
   ```
   https://bill-extraction-api-XXXX.onrender.com/extract-bill-data
   ```

**This is your public API endpoint!**

---

## Step 6: Test Your API

```bash
curl -X POST https://bill-extraction-api-XXXX.onrender.com/extract-bill-data \
  -H "Content-Type: application/json" \
  -d '{"document": "https://example.com/bill.png"}'
```

You should get:
```json
{
  "is_success": false,  // Because example.com/bill.png doesn't exist
  "token_usage": {"total_tokens": 0, "input_tokens": 0, "output_tokens": 0},
  "data": null,
  "error": "..."
}
```

---

## Step 7: Test with Real Bill

Get a bill image URL from the Bajaj training samples:

```bash
curl -X POST https://bill-extraction-api-XXXX.onrender.com/extract-bill-data \
  -H "Content-Type: application/json" \
  -d '{
    "document": "https://your-sample-bill.png"
  }'
```

Expected response:
```json
{
  "is_success": true,
  "token_usage": {"total_tokens": 0, "input_tokens": 0, "output_tokens": 0},
  "data": {
    "pagewise_line_items": [...],
    "total_item_count": 12,
    "reconciled_amount": 2500.0
  },
  "error": null
}
```

---

## Step 8: Submit to Datathon

Copy your URL:
```
https://bill-extraction-api-XXXX.onrender.com/extract-bill-data
```

Paste it into the datathon submission portal under "Webhook URL"

**Done!** ✅

---

## Important Notes

### Cold Start

First request after deploy may take 10-15 seconds (container is waking up).  
Subsequent requests: 2-5 seconds.

### Auto-Sleep

Render free tier auto-sleeps after 30 minutes of inactivity.  
API wakes automatically on next request.

### Logs

To see what's happening:
1. Go to Render dashboard
2. Click your service
3. Click **Logs** tab

---

## Troubleshooting

### "Deploy Failed"

Check Render logs for error. Common issues:
- Python version mismatch
- Missing dependencies
- Docker syntax error

**Solution:** Check logs in Render dashboard

### "No text detected"

API is working, but bill image quality is poor.

**Solution:** Try with higher quality image (1500+ pixels width)

### "Failed to download document"

Document URL is invalid or inaccessible.

**Solution:** Ensure URL is publicly accessible and HTTPS

---

## Next Steps

1. ✅ Deploy to Render
2. ✅ Get public webhook URL
3. ✅ Test with sample bills
4. ✅ Submit to datathon
5. Optional: Improve accuracy by fine-tuning on your 15 sample bills

---

## Support

- Full documentation: See README.md
- API docs: `https://bill-extraction-api-XXXX.onrender.com/docs`
- Health check: `https://bill-extraction-api-XXXX.onrender.com/health`

---

**🎉 Congratulations!** You now have a live, public bill extraction API!

**Time taken:** 5-10 minutes  
**Cost:** $0  
**Ready for submission:** YES ✅
