# Phase 2-4 Upgrade Guide: AI Personalization & Media Enhancement

This guide walks you through upgrading your News App with advanced AI personalization, reading contexts, and YouTube/Podcast metadata extraction.

## 🎯 What's New

### Phase 2: Enhanced AI Scoring
- **User Preference Learning**: System learns from your thumbs up/down feedback
- **Personalized Scoring**: Articles ranked based on your interests
- **Category Preferences**: Automatically weighs categories based on feedback
- **Content Depth Classification**: Articles tagged as light/medium/heavy

### Phase 3: Smart Curation
- **Trend Detection**: Identifies popular topics across sources
- **Serendipity Algorithm**: Surfaces unexpected but interesting content
- **Comprehensive Scoring**: Combines AI relevance + personalization + trends + serendipity

### Phase 4: YouTube & Podcast Metadata
- **YouTube Metadata**: Auto-extracts duration, views, channel name
- **Podcast Metadata**: Extracts duration and author info
- **Rich Display**: Show video length and author in UI

---

## 📦 Installation Steps

### Step 1: Update Dependencies

```bash
cd /path/to/News\ App
pip install -r requirements.txt
```

This will install:
- `yt-dlp`: For YouTube metadata extraction (no API key needed!)
- Already installed: `djangorestframework`

### Step 2: Create Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

This creates the new models:
- `UserPreference`: Stores learned interests and category weights
- `ReadingContext`: Mood/context presets (Morning Briefing, Deep Dive, etc.)
- Updated `Article` model with new fields:
  - `personalization_score`, `trend_score`, `serendipity_score`
  - `duration_seconds`, `author`, `view_count` (for YouTube/podcasts)
  - `content_depth` (light/medium/heavy)

### Step 3: Set Up Reading Contexts

```bash
python manage.py setup_contexts
```

This creates 5 default reading contexts:
- ☀️ **Morning Briefing**: Light content, trending topics
- 🔍 **Deep Dive**: Long-form, in-depth articles
- ⚖️ **Balanced**: Mix of everything (default)
- 🎲 **Discovery Mode**: High serendipity, explore new topics
- 🔥 **Trending Topics**: Focus on what's popular now

### Step 4: Update User Preferences (Optional)

If you already have articles with feedback:

```bash
python manage.py curate_content --update-preferences
```

This analyzes your existing likes/dislikes and builds your preference profile.

### Step 5: Enrich Existing YouTube/Podcast Articles

```bash
# Enrich first 20 YouTube/podcast articles
python manage.py enrich_media

# Or enrich all:
python manage.py enrich_media --all
```

This extracts metadata for existing videos and podcasts.

---

## 🎮 How to Use

### 1. Switch Reading Contexts

Click on any reading mode in the sidebar (left panel):
- ☀️ Morning Briefing
- 🔍 Deep Dive
- ⚖️ Balanced
- 🎲 Discovery Mode
- 🔥 Trending Topics

Articles will be re-ranked based on the context you choose!

### 2. Give Feedback

Continue using 👍 👎 on articles. Every 10 feedbacks, the system automatically:
- Updates your keyword interests
- Adjusts category preferences
- Refines personalization scores

### 3. Run AI Curation

Now enhanced with personalization:

```bash
python manage.py curate_content
```

This command now:
1. Summarizes articles (as before)
2. AI scores relevance (now uses your interests!)
3. Classifies content depth (light/medium/heavy)
4. Calculates personalized scores (relevance + personalization + trends + serendipity)

**Pro tip**: Run with `--update-preferences` occasionally to refresh your learned profile:

```bash
python manage.py curate_content --update-preferences
```

### 4. Automatic Enrichment

New YouTube/podcast articles synced via n8n are automatically enriched with metadata!

---

## 🔧 How It Works

### Scoring Algorithm

Each article gets 4 scores:

1. **Relevance Score (0-100)**: AI-based relevance to your interests
2. **Personalization Score (0-100)**: Based on your feedback history
   - Category preferences (+/- 20 points)
   - Source preferences (+/- 15 points)
   - Keyword matches (up to +20 points)
   - Content depth match (+/- 10 points)
3. **Trend Score (0-100)**: How popular/trending the topic is
4. **Serendipity Score (0-100)**: How unexpected but potentially interesting

**Final Score** = Weighted combination based on active reading context:
- Balanced: 40% relevance, 30% personalization, 20% trend, 10% serendipity
- Deep Dive: 40% relevance, 40% personalization, 10% trend, 10% serendipity
- Discovery Mode: 20% relevance, 20% personalization, 20% trend, 40% serendipity
- etc.

### Preference Learning

The system tracks:
- **Liked articles**: Extracts keywords, notes categories/sources
- **Disliked articles**: Reduces weight for those categories/sources
- **Category weights**: Between -1 (always disliked) and +1 (always liked)
- **Top keywords**: 20 most common words from liked article titles

Updates happen:
- Automatically every 10 feedbacks
- Manually via `--update-preferences` flag
- Visible in curation command output

---

## 📊 Monitoring Your Profile

Check your learned preferences:

```bash
python manage.py curate_content
```

The output shows:
```
User: admin
Total feedback: 47
Top interests: machine, learning, climate, startup, technology
```

---

## 🎨 UI Updates

The sidebar now includes:
- **Reading Mode section**: Switch contexts on the fly
- **Active context highlighted**: Shows current mode with colored background

Articles are now sorted by:
- Personalization score (primary)
- Publication date (fallback)

---

## 🚀 Advanced: Customizing Reading Contexts

You can create custom reading contexts via Django admin:

1. Go to `/admin/news/readingcontext/`
2. Add new reading context
3. Set weights:
   - `relevance_weight`: How much to value AI relevance
   - `personalization_weight`: How much to value your history
   - `serendipity_weight`: How much to explore new topics
   - `trend_weight`: How much to follow trending topics
4. Choose enabled categories (optional)
5. Set content depth filter (light/medium/heavy)

**Example Custom Context: "AI Only, Deep"**
- Categories: AI, Tech
- Content Depth: Heavy
- Weights: 50% personalization, 40% relevance, 5% trend, 5% serendipity

---

## 🐛 Troubleshooting

### YouTube Metadata Not Extracting

**Problem**: `enrich_media` command fails or doesn't extract data

**Solutions**:
1. Check if yt-dlp is installed:
   ```bash
   yt-dlp --version
   ```
2. Update yt-dlp (it breaks frequently due to YouTube changes):
   ```bash
   pip install --upgrade yt-dlp
   ```
3. Some videos may be region-blocked or deleted (this is normal)

### User Preferences Not Updating

**Problem**: Feedback doesn't seem to affect article ranking

**Solutions**:
1. Give at least 10 feedbacks (updates happen every 10)
2. Manually trigger update:
   ```bash
   python manage.py curate_content --update-preferences
   ```
3. Run curation to recalculate scores:
   ```bash
   python manage.py curate_content
   ```
4. Check that articles have `personalization_score > 0`

### Reading Contexts Not Showing

**Problem**: Sidebar doesn't show reading modes

**Solutions**:
1. Make sure you ran `setup_contexts` command
2. Check contexts exist: `/admin/news/readingcontext/`
3. Verify base template was updated (should show context switcher)

### Content Depth Not Classified

**Problem**: All articles show `content_depth = 'medium'`

**Solutions**:
1. Run curation command (step 3 classifies content depth)
2. Check GEMINI_API_KEY is set in `.env`
3. Classification only runs for articles with `content_depth='medium'`

---

## 🔄 Maintenance Tasks

### Daily/Hourly (via n8n workflow)
```bash
python manage.py fetch_feeds  # Or via n8n sync
python manage.py curate_content
```

### Weekly (Recommended)
```bash
# Refresh user preferences
python manage.py curate_content --update-preferences

# Enrich new YouTube/podcast articles
python manage.py enrich_media --limit 50
```

### Monthly
```bash
# Update yt-dlp
pip install --upgrade yt-dlp

# Re-classify content depth (algorithm may improve)
python manage.py curate_content
```

---

## 📈 Performance Tips

### API Cost Optimization

**Gemini API** (free tier: 15 RPM, 1,500 req/day):
- Batch scoring: 50 articles per request ✅
- Content classification: ~50 requests per curation run
- Summarization: Only for articles > 500 chars

**yt-dlp** (free, no API key):
- No quota limits
- Can be slow (5-10 seconds per video)
- Run `enrich_media` during off-hours

**Recommendations**:
- Run curation every 6-12 hours (not hourly)
- Use `--limit` flags to process incrementally
- Only enrich new YouTube articles (automatic via serializer)

---

## ✅ Next Steps

After upgrading:

1. ✅ Run migrations
2. ✅ Set up reading contexts
3. ✅ Update preferences (if you have feedback)
4. ✅ Enrich media (YouTube/podcasts)
5. ✅ Test context switching in UI
6. ✅ Give feedback on articles to train personalization
7. ✅ Update n8n workflow (optional: filter by category/context)

---

## 🎯 Future Enhancements (Not in this release)

Ideas for Phase 5+:
- **PocketCast API Integration**: Sync podcast listening history
- **YouTube Watch History**: Import from YouTube Data API
- **Multi-user Support**: Different preferences per user
- **Mobile App**: React Native app with push notifications
- **Voice Summary**: TTS for article summaries
- **Smart Digests**: Daily email with top personalized articles

Want any of these? Let me know!

---

## 🆘 Getting Help

If you encounter issues:
1. Check Django logs: Terminal where `runserver` is running
2. Check n8n logs: Workflow → Executions tab
3. Verify .env variables are set (GEMINI_API_KEY, etc.)
4. Run `python manage.py check` to verify configuration

---

Happy reading! 📰✨
