# Quick Start: FreshRSS → Django Integration

## ⚡ 5-Minute Setup

### Step 1: Update .env

Add your API token to [.env](.env):

```env
N8N_API_TOKEN=1f3327082d4f3f086253001e7056c06915de23e2
```

### Step 2: Start Django Server

```bash
python manage.py runserver 0.0.0.0:8000
```

> Make sure your Django server is accessible from n8n (same network or via reverse proxy)

### Step 3: Test API

```bash
curl -H "Authorization: Token 1f3327082d4f3f086253001e7056c06915de23e2" \
  http://localhost:8000/api/stats/
```

Expected response:
```json
{
  "total_articles": 123,
  "unread_articles": 45,
  "saved_articles": 12,
  "total_sources": 8
}
```

### Step 4: Create n8n Credentials

**FreshRSS Credential (HTTP Basic Auth):**
- User: Your FreshRSS username
- Password: Your FreshRSS API password (from FreshRSS → Settings → Authentication)

**Django Credential (Header Auth):**
- Name: `Authorization`
- Value: `Token 1f3327082d4f3f086253001e7056c06915de23e2`

### Step 5: Import n8n Workflow

1. Copy the workflow JSON from [N8N_INTEGRATION.md](N8N_INTEGRATION.md)
2. In n8n: **Import from File** → Paste JSON
3. Update URLs:
   - FreshRSS: `http://your-freshrss-ip/api/greader.php/reader/api/0/stream/contents/reading-list`
   - Django: `http://your-django-ip:8000/api/`
4. Add credentials to each HTTP node
5. **Activate** the workflow

### Step 6: Test the Workflow

Click **Execute Workflow** in n8n to run it manually.

---

## 🎯 What This Does

1. **Every hour**, n8n fetches unread articles from FreshRSS
2. **Transforms** the data to Django format
3. **Sends** articles to Django API in batches
4. **Triggers** AI curation (Gemini scoring & summarization)
5. **You** see personalized articles in the Django app

---

## 📊 URLs

- **FreshRSS**: http://your-homelab-ip:freshrss-port
- **Django App**: http://your-homelab-ip:8000
- **Django API**: http://your-homelab-ip:8000/api/
- **n8n**: http://your-homelab-ip:5678

---

## 🔧 Troubleshooting

**Articles not syncing?**
- Check n8n execution logs (click on the workflow execution)
- Verify FreshRSS API is accessible from n8n
- Verify Django API is accessible from n8n
- Check authentication tokens

**Need help?**
- See full documentation: [N8N_INTEGRATION.md](N8N_INTEGRATION.md)
- Check Django logs: Terminal where `runserver` is running
- Check n8n logs: Workflow → Executions tab

---

## ✅ Next Steps

Once syncing works:
- [ ] Add more sources to FreshRSS
- [ ] Fine-tune AI scoring (Phase 2)
- [ ] Add user preference learning
- [ ] Build mood/context selector UI
