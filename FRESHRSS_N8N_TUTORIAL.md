# Complete FreshRSS & n8n Tutorial for Beginners

This guide assumes you have Docker containers for FreshRSS and n8n running on your homelab, but you're not sure how to use them. We'll walk through everything step-by-step.

---

## 📚 Table of Contents

1. [What are FreshRSS and n8n?](#what-are-freshrss-and-n8n)
2. [Part 1: Setting Up FreshRSS](#part-1-setting-up-freshrss)
3. [Part 2: Setting Up n8n](#part-2-setting-up-n8n)
4. [Part 3: Connecting Everything](#part-3-connecting-everything)
5. [Part 4: Testing the Full Flow](#part-4-testing-the-full-flow)
6. [Troubleshooting](#troubleshooting)

---

## What are FreshRSS and n8n?

### **FreshRSS** 📰
Think of FreshRSS as your personal news collector. It:
- Checks RSS feeds from websites you choose (every hour or so)
- Organizes articles by category
- Marks what's read/unread
- Provides an API so other tools can access your articles

**Why use it?** Instead of Django checking 50 RSS feeds separately (slow, inefficient), FreshRSS does it once and Django just reads from FreshRSS.

### **n8n** 🔄
Think of n8n as a delivery truck. It:
- Picks up articles from FreshRSS
- Transforms them into Django format
- Delivers them to your Django API
- Runs automatically on a schedule

**Why use it?** It connects FreshRSS and Django without you writing any code. Plus you can see exactly what's happening with visual workflows.

### **The Full Flow**
```
Websites (TechCrunch, Ars Technica, etc.)
        ↓
    FreshRSS (collects & organizes)
        ↓
    n8n (transforms & delivers)
        ↓
    Django API (stores & personalizes)
        ↓
    You (read in beautiful UI!)
```

---

## Part 1: Setting Up FreshRSS

### Step 1: Access FreshRSS

1. Open your browser
2. Go to: `http://your-homelab-ip:freshrss-port`
   - Example: `http://192.168.1.100:8080`
   - (Check your Docker setup for the exact port)

3. You should see FreshRSS login/setup screen

### Step 2: Initial Setup (First Time Only)

If this is your first time:

1. **Choose language**: English
2. **Create admin account**:
   - Username: `admin` (or whatever you prefer)
   - Password: Choose a strong password
   - Email: Your email
3. Click **Submit**

### Step 3: Add Your First RSS Feed

Let's add TechCrunch as an example:

1. Click **Subscription** in the top menu
2. Click **+ Add a feed**
3. Enter feed URL:
   ```
   https://techcrunch.com/feed/
   ```
4. Click **Add**
5. FreshRSS will verify the feed and show you a preview
6. **Choose a category**:
   - Click "Create new category"
   - Name: `Tech`
   - Color: Pick any color you like
   - Click **Add**
7. Click **Add** to confirm

🎉 You just added your first feed!

### Step 4: Add More Feeds

Here are some popular feeds to get started:

**Tech:**
- TechCrunch: `https://techcrunch.com/feed/`
- Ars Technica: `https://feeds.arstechnica.com/arstechnica/index`
- The Verge: `https://www.theverge.com/rss/index.xml`
- Hacker News: `https://hnrss.org/frontpage`

**AI:**
- OpenAI Blog: `https://openai.com/blog/rss/`
- AI Weekly: `http://aiweekly.co/rss`

**World News:**
- BBC: `http://feeds.bbci.co.uk/news/rss.xml`
- Reuters: `https://www.reutersagency.com/feed/`
- NPR: `https://feeds.npr.org/1001/rss.xml`

**YouTube Channels:**
YouTube channels have RSS feeds too! Format:
```
https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
```

To find a channel's ID:
1. Go to the channel page
2. View page source (Ctrl+U)
3. Search for "channelId"
4. Copy the ID (looks like: `UCXuqSBlHAE6Xw-yeJA0Tunw`)

**Example YouTube feeds:**
- Two Minute Papers: `https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg`
- Fireship: `https://www.youtube.com/feeds/videos.xml?channel_id=UCsBjURrPoezykLs9EqgamOA`

### Step 5: Create Categories

Organize your feeds into categories:

1. Click **Settings** → **Categories**
2. Create categories like:
   - Tech
   - AI
   - World News
   - Health
   - Sport
   - YouTube
   - Podcasts

3. Go back to **Subscription**
4. For each feed, click the **edit** icon (pencil)
5. Assign it to the appropriate category

### Step 6: Enable API Access

This is crucial for n8n to access your feeds:

1. Click **Settings** → **Authentication**
2. Scroll to **API password (Google Reader format)**
3. Click **Generate new API password**
4. **Save this password somewhere safe!** You'll need it for n8n
5. Your username for API: Same as your FreshRSS username (e.g., `admin`)

Example:
```
API Username: admin
API Password: a1b2c3d4e5f6g7h8
```

### Step 7: Test FreshRSS

1. Click **Unread** in top menu
2. You should see articles from your feeds!
3. Click an article to read it
4. Try marking some as read/unread

**Tip:** FreshRSS will check feeds every hour by default. You can manually refresh by clicking **Refresh feeds** button.

---

## Part 2: Setting Up n8n

### Step 1: Access n8n

1. Open browser
2. Go to: `http://your-homelab-ip:5678`
   - Example: `http://192.168.1.100:5678`

3. You should see n8n interface

### Step 2: Initial Setup (First Time Only)

If first time:

1. Create account:
   - Email: Your email
   - Password: Choose a password
2. Click **Get started**

### Step 3: Understand the n8n Interface

**Key concepts:**

- **Workflow**: A sequence of tasks (like a recipe)
- **Node**: A single step in the workflow
- **Trigger**: What starts the workflow (e.g., "every hour")
- **Credential**: Login info for services (FreshRSS, Django)

### Step 4: Create Your First Workflow

1. Click **+ Add workflow** (top right)
2. You'll see an empty canvas
3. Click the **+** button in the center

You'll see a node selection menu. Let's build the workflow step by step!

### Step 5: Add Schedule Trigger

**What it does:** Runs the workflow every hour automatically.

1. In node search, type: `Schedule`
2. Click **Schedule Trigger**
3. Configure:
   - **Trigger Interval**: `Hours`
   - **Hours Between Triggers**: `1`
4. Click **Execute Node** to test (should show current timestamp)

### Step 6: Add FreshRSS HTTP Request

**What it does:** Fetches unread articles from FreshRSS.

1. Click the **+** after Schedule node
2. Search for: `HTTP Request`
3. Click **HTTP Request**
4. Configure:
   - **Method**: `GET`
   - **URL**: `http://your-freshrss-ip:port/api/greader.php/reader/api/0/stream/contents/reading-list`
     - Example: `http://192.168.1.100:8080/api/greader.php/reader/api/0/stream/contents/reading-list`
   - **Query Parameters**: Click "Add Parameter" twice:
     - Parameter 1: `n` = `50` (fetch 50 articles)
     - Parameter 2: `xt` = `user/-/state/com.google/read` (exclude read articles)
   - **Authentication**: `Basic Auth`

5. Click **Create New Credential** (credential selector dropdown)
6. Configure credential:
   - **Name**: `FreshRSS API`
   - **User**: Your FreshRSS username (e.g., `admin`)
   - **Password**: Your FreshRSS API password (from Part 1, Step 6)
   - Click **Create**

7. Click **Execute Node** to test
8. You should see JSON with your articles! (Click "JSON" tab to see)

**Example output:**
```json
{
  "items": [
    {
      "id": "tag:google.com,2005:reader/item/...",
      "title": "New AI Model Announced",
      "published": 1234567890,
      "origin": {
        "title": "TechCrunch",
        "htmlUrl": "https://techcrunch.com"
      },
      ...
    }
  ]
}
```

### Step 7: Add Code Node (Transform Data)

**What it does:** Converts FreshRSS format to Django format.

1. Click **+** after HTTP Request node
2. Search for: `Code`
3. Click **Code**
4. **Language**: `JavaScript`
5. **Mode**: `Run Once for All Items`
6. Paste this code:

```javascript
// Get FreshRSS data
const items = $input.all();
const freshRSSData = items[0].json;

// Transform to Django format
const articles = freshRSSData.items.map(item => {
  // Extract category from item.categories
  let categorySlug = 'general';
  if (item.categories && item.categories.length > 0) {
    // FreshRSS categories look like "user/123/label/Tech"
    const labelMatch = item.categories[0].match(/label\/(.*?)$/);
    if (labelMatch) {
      categorySlug = labelMatch[1].toLowerCase().replace(/\s+/g, '-');
    }
  }

  // Detect source type
  let sourceType = 'rss';
  if (item.origin?.streamId?.includes('youtube.com') || item.origin?.htmlUrl?.includes('youtube.com')) {
    sourceType = 'yt';
  } else if (item.origin?.title?.toLowerCase().includes('podcast')) {
    sourceType = 'podcast';
  }

  return {
    title: item.title,
    link: item.alternate?.[0]?.href || item.id,
    description: item.summary?.content || item.content?.content || '',
    pub_date: new Date(item.published * 1000).toISOString(),
    guid: item.id,
    source_name: item.origin?.title || 'Unknown',
    source_url: item.origin?.htmlUrl || item.origin?.streamId || '',
    category_slug: categorySlug,
    source_type: sourceType,
    image_url: item.enclosure?.[0]?.href || ''
  };
});

return [{ json: { articles } }];
```

7. Click **Execute Node** to test
8. You should see transformed data in Django format!

### Step 8: Add Django HTTP Request (Send Articles)

**What it does:** Sends articles to your Django API.

1. Click **+** after Code node
2. Search: `HTTP Request`
3. Click **HTTP Request**
4. Configure:
   - **Method**: `POST`
   - **URL**: `http://your-django-ip:8000/api/ingest/articles/`
     - Example: `http://192.168.1.100:8000/api/ingest/articles/`
     - **Important**: Use the IP where Django is running (might be same as FreshRSS or different)
   - **Send Body**: `Yes`
   - **Body Content Type**: `JSON`
   - **Body**: `={{ JSON.stringify($json.articles) }}`
   - **Authentication**: `Generic Credential Type`
   - **Generic Auth Type**: `Header Auth`

5. Click **Create New Credential**
6. Configure:
   - **Name**: `Django API Token`
   - **Header Name**: `Authorization`
   - **Header Value**: `Token 1f3327082d4f3f086253001e7056c06915de23e2`
     - (Use YOUR token from `.env` file)
   - Click **Create**

7. **Don't execute yet** - Django needs to be running first!

### Step 9: Add Django HTTP Request (Trigger Curation)

**What it does:** Tells Django to run AI curation after ingesting articles.

1. Click **+** after previous HTTP Request
2. Search: `HTTP Request`
3. Click **HTTP Request**
4. Configure:
   - **Method**: `POST`
   - **URL**: `http://your-django-ip:8000/api/curate/`
   - **Authentication**: `Generic Credential Type`
   - **Generic Auth Type**: `Header Auth`
   - **Credential**: Select `Django API Token` (reuse from previous step)

5. **Don't execute yet** - we'll test the full flow next!

### Step 10: Name and Save Workflow

1. Click workflow name at top (says "My workflow")
2. Rename to: `FreshRSS to Django Sync`
3. Click **Save** (top right)

### Step 11: Activate Workflow

1. Toggle the **Active** switch (top right)
2. It should turn green
3. Your workflow now runs every hour automatically! ✅

---

## Part 3: Connecting Everything

### Step 1: Verify Network Connectivity

All three services need to talk to each other:

**If everything is on the same Docker network:**
- Use container names: `http://freshrss:port`, `http://n8n:5678`, `http://django:8000`

**If using host network or different networks:**
- Use IP addresses: `http://192.168.1.100:port`

**To test connectivity from n8n:**

1. Create a simple workflow
2. Add HTTP Request node
3. Try accessing Django: `http://your-django-ip:8000/api/stats/`
4. Use your Django API token
5. Execute - should return stats

### Step 2: Start Django Server

On your homelab where Django is:

```bash
cd /path/to/News\ App
python manage.py runserver 0.0.0.0:8000
```

**Important:** Use `0.0.0.0:8000` not `127.0.0.1:8000` so it's accessible from other containers!

### Step 3: Test Django API from n8n

In n8n:

1. Open your workflow
2. Click on the "Send to Django" HTTP Request node
3. Click **Execute Node**
4. Should see success response with article IDs

If you get errors:
- Check Django is running
- Check URL is correct
- Check token matches your `.env` file
- Check Django logs for errors

### Step 4: Test Full Workflow

1. Click **Execute Workflow** (top right in n8n)
2. Watch each node execute (they'll turn green)
3. Check for errors (red nodes)
4. At the end, you should see:
   - Articles fetched from FreshRSS ✅
   - Data transformed ✅
   - Articles sent to Django ✅
   - AI curation triggered ✅

### Step 5: Verify in Django

1. Open Django app: `http://your-django-ip:8000`
2. Log in
3. You should see articles from FreshRSS!
4. Check if they have AI summaries (might take a few minutes for curation to complete)

---

## Part 4: Testing the Full Flow

### End-to-End Test

Let's make sure everything works:

#### 1. Add a New Article to FreshRSS

1. Go to FreshRSS
2. Find an unread article
3. Keep it unread

#### 2. Trigger n8n Workflow Manually

1. Go to n8n
2. Open your workflow
3. Click **Execute Workflow**
4. Wait for all nodes to turn green

#### 3. Check Django

1. Go to Django app
2. Refresh the dashboard
3. The new article should appear!

#### 4. Test AI Features

1. Wait a few minutes for curation to run (or run manually):
   ```bash
   python manage.py curate_content
   ```

2. Refresh Django app
3. Article should now have:
   - AI summary ✅
   - Relevance score ✅
   - Personalization score ✅

#### 5. Test Feedback Loop

1. Click 👍 on an article
2. Check that feedback is saved (article should highlight)
3. After 10 feedbacks, preferences update automatically
4. Or manually:
   ```bash
   python manage.py curate_content --update-preferences
   ```

### Automated Schedule Test

1. Wait 1 hour (or change workflow to every 5 minutes for testing)
2. n8n should automatically run
3. Check **Executions** tab in n8n to see runs
4. New articles should appear in Django

---

## Part 5: Daily Usage

### Morning Routine

1. **Check FreshRSS** (optional):
   - See what new articles came in
   - You can star/mark articles here if you want

2. **Open Django App**:
   - All articles are already synced!
   - AI has already scored and summarized them
   - Just read your personalized feed

3. **Give Feedback**:
   - 👍 articles you like
   - 👎 articles you don't
   - System learns your preferences

### Weekly Maintenance

1. **Update Preferences** (if you gave lots of feedback):
   ```bash
   python manage.py curate_content --update-preferences
   ```

2. **Enrich Media** (for YouTube/podcasts):
   ```bash
   python manage.py enrich_media --limit 20
   ```

3. **Check n8n Executions**:
   - Go to n8n → Workflows → Your workflow → Executions
   - Make sure all recent runs succeeded
   - If failures, check what went wrong

### Troubleshooting

**Articles not syncing?**

1. Check FreshRSS has unread articles
2. Check n8n workflow is Active (toggle in top right)
3. Check n8n Executions tab for errors
4. Manually execute workflow to see what fails

**AI not scoring articles?**

1. Check GEMINI_API_KEY in `.env`
2. Run curation manually:
   ```bash
   python manage.py curate_content
   ```
3. Check Django terminal for errors

**YouTube metadata not working?**

1. Check yt-dlp is installed:
   ```bash
   yt-dlp --version
   ```
2. Update yt-dlp:
   ```bash
   pip install --upgrade yt-dlp
   ```

---

## Common Issues

### Issue 1: n8n can't reach FreshRSS

**Symptoms:** HTTP Request node fails with "Connection refused"

**Solution:**
- Check FreshRSS is running: `docker ps`
- Verify URL includes port: `http://ip:port/api/...`
- If same Docker network, try container name: `http://freshrss:80/api/...`
- Test in browser first: Can you access FreshRSS web UI?

### Issue 2: Django not receiving articles

**Symptoms:** n8n shows success but no articles in Django

**Solutions:**
- Check Django is running: `python manage.py runserver 0.0.0.0:8000`
- Check API token matches `.env` file
- Check Django logs for errors
- Test API manually:
  ```bash
  curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8000/api/stats/
  ```

### Issue 3: Articles duplicating

**Symptoms:** Same article appears multiple times

**Solution:**
- Articles are deduplicated by GUID
- Check that GUIDs are unique in n8n transform code
- Existing articles are updated, not duplicated

### Issue 4: FreshRSS not fetching new articles

**Symptoms:** No new articles appearing

**Solutions:**
- Click "Refresh" button in FreshRSS manually
- Check feed URLs are still valid
- Check FreshRSS logs: `docker logs freshrss-container`
- Some feeds update slowly (hourly/daily)

---

## Next Steps

After everything is working:

1. ✅ Add more feeds to FreshRSS
2. ✅ Give feedback to train personalization
3. ✅ Try different reading contexts (☀️ 🔍 ⚖️ 🎲 🔥)
4. ✅ Run enrichment for YouTube videos
5. ✅ Create custom reading contexts in Django admin

---

## Advanced Tips

### Adjust n8n Schedule

Edit the Schedule Trigger node:
- Every 30 minutes: Good for high-volume feeds
- Every 2 hours: Good for low-volume feeds
- Specific times: Run at 7am, 12pm, 6pm only

### Filter Articles in n8n

Add an IF node between Code and Django nodes to filter:
- Only articles with images
- Only certain categories
- Only articles longer than X characters

### Multiple Workflows

Create separate workflows for:
- Urgent news (every 30 min)
- Deep reads (daily digest)
- YouTube only (hourly)

### Backup Your Data

**FreshRSS:**
```bash
docker exec freshrss-container php /var/www/FreshRSS/app/i18n/export.php
```

**Django:**
```bash
python manage.py dumpdata > backup.json
```

---

## Helpful Commands

**Check what's running:**
```bash
docker ps
```

**View logs:**
```bash
docker logs freshrss-container
docker logs n8n-container
```

**Restart container:**
```bash
docker restart freshrss-container
docker restart n8n-container
```

**Django management:**
```bash
python manage.py curate_content
python manage.py curate_content --update-preferences
python manage.py enrich_media --limit 20
python manage.py setup_contexts
```

---

## Resources

- **FreshRSS Docs**: https://freshrss.github.io/FreshRSS/en/
- **n8n Docs**: https://docs.n8n.io/
- **RSS Feed Finder**: https://rss.app/ (find RSS feeds for any site)
- **YouTube Channel ID Finder**: https://commentpicker.com/youtube-channel-id.php

---

You're all set! 🎉

Any questions? Check the troubleshooting section or the Django/n8n logs for more details.
