# n8n Integration Guide

This guide shows how to connect FreshRSS to your Django News App using n8n.

## Architecture

```
FreshRSS → n8n → Django API → AI Processing
```

## Setup Steps

### 1. Prerequisites

- ✅ FreshRSS running on your homelab
- ✅ n8n running on your homelab
- ✅ Django app accessible from n8n (same network or exposed via reverse proxy)
- ✅ API token generated (see below)

### 2. Get Your API Token

Your API token has been generated:

```
Token: 1f3327082d4f3f086253001e7056c06915de23e2
```

**Add to your Django .env file:**
```env
N8N_API_TOKEN=1f3327082d4f3f086253001e7056c06915de23e2
```

### 3. Django API Endpoints

Base URL: `http://your-django-server:8000/api/`

All requests require authentication header:
```
Authorization: Token 1f3327082d4f3f086253001e7056c06915de23e2
```

#### Available Endpoints

**1. Ingest Single Article**
```
POST /api/ingest/article/
Content-Type: application/json

{
    "title": "Article Title",
    "link": "https://example.com/article",
    "description": "Article content...",
    "pub_date": "2024-01-01T00:00:00Z",
    "guid": "unique-id",
    "source_name": "TechCrunch",
    "source_url": "https://techcrunch.com/feed",
    "category_slug": "tech",
    "source_type": "rss",  // or "yt", "podcast"
    "image_url": "https://example.com/image.jpg"
}
```

**2. Ingest Multiple Articles (Batch)**
```
POST /api/ingest/articles/
Content-Type: application/json

{
    "articles": [
        {
            "title": "Article 1",
            "link": "https://...",
            ...
        },
        {
            "title": "Article 2",
            "link": "https://...",
            ...
        }
    ]
}
```

**3. Trigger AI Curation**
```
POST /api/curate/
```

**4. Get Stats**
```
GET /api/stats/
```

**5. List Sources**
```
GET /api/sources/
```

### 4. FreshRSS API Setup

FreshRSS supports Fever API and Google Reader API for syncing.

**Get API Password:**
1. Go to FreshRSS Settings → Authentication
2. Create an API password
3. Note your username and API password

**FreshRSS API Endpoints:**
- Base URL: `http://your-freshrss-server/api/greader.php`
- Authentication: Basic Auth or query params

**Example API calls:**

Get unread items:
```
GET http://freshrss/api/greader.php/reader/api/0/stream/contents/reading-list?n=50&xt=user/-/state/com.google/read
```

## n8n Workflow Templates

### Option 1: Simple Polling Workflow (Recommended for Start)

This workflow polls FreshRSS every hour and syncs new articles.

#### Workflow Structure:
1. **Schedule Trigger** → Every 1 hour
2. **HTTP Request** → Fetch unread articles from FreshRSS
3. **Function** → Transform FreshRSS data to Django format
4. **HTTP Request** → Send to Django API (batch)
5. **HTTP Request** → Trigger AI curation

#### n8n Workflow JSON:

```json
{
  "name": "FreshRSS to Django Sync",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "hours",
              "hoursInterval": 1
            }
          ]
        }
      },
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "url": "http://your-freshrss-server/api/greader.php/reader/api/0/stream/contents/reading-list",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpBasicAuth",
        "sendQuery": true,
        "queryParameters": {
          "parameters": [
            {
              "name": "n",
              "value": "50"
            },
            {
              "name": "xt",
              "value": "user/-/state/com.google/read"
            }
          ]
        }
      },
      "name": "Fetch FreshRSS Articles",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [450, 300],
      "credentials": {
        "httpBasicAuth": {
          "name": "FreshRSS API"
        }
      }
    },
    {
      "parameters": {
        "jsCode": "const items = $input.all();\nconst freshRSSData = items[0].json;\n\n// Transform FreshRSS items to Django format\nconst articles = freshRSSData.items.map(item => {\n  // Extract category from item.categories\n  let categorySlug = 'general';\n  if (item.categories && item.categories.length > 0) {\n    // FreshRSS categories are like \"user/123/label/Tech\"\n    const labelMatch = item.categories[0].match(/label\\/(.*?)$/);\n    if (labelMatch) {\n      categorySlug = labelMatch[1].toLowerCase().replace(/\\s+/g, '-');\n    }\n  }\n\n  // Detect source type\n  let sourceType = 'rss';\n  if (item.origin?.streamId?.includes('youtube.com') || item.origin?.htmlUrl?.includes('youtube.com')) {\n    sourceType = 'yt';\n  } else if (item.origin?.title?.toLowerCase().includes('podcast')) {\n    sourceType = 'podcast';\n  }\n\n  return {\n    title: item.title,\n    link: item.alternate?.[0]?.href || item.id,\n    description: item.summary?.content || item.content?.content || '',\n    pub_date: new Date(item.published * 1000).toISOString(),\n    guid: item.id,\n    source_name: item.origin?.title || 'Unknown',\n    source_url: item.origin?.htmlUrl || item.origin?.streamId || '',\n    category_slug: categorySlug,\n    source_type: sourceType,\n    image_url: item.enclosure?.[0]?.href || ''\n  };\n});\n\nreturn [{ json: { articles } }];"
      },
      "name": "Transform Data",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [650, 300]
    },
    {
      "parameters": {
        "url": "http://your-django-server:8000/api/ingest/articles/",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "articles",
              "value": "={{ $json.articles }}"
            }
          ]
        }
      },
      "name": "Send to Django",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [850, 300],
      "credentials": {
        "httpHeaderAuth": {
          "name": "Django API Token"
        }
      }
    },
    {
      "parameters": {
        "url": "http://your-django-server:8000/api/curate/",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "method": "POST"
      },
      "name": "Trigger AI Curation",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [1050, 300],
      "credentials": {
        "httpHeaderAuth": {
          "name": "Django API Token"
        }
      }
    }
  ],
  "connections": {
    "Schedule Trigger": {
      "main": [
        [
          {
            "node": "Fetch FreshRSS Articles",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Fetch FreshRSS Articles": {
      "main": [
        [
          {
            "node": "Transform Data",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Transform Data": {
      "main": [
        [
          {
            "node": "Send to Django",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Send to Django": {
      "main": [
        [
          {
            "node": "Trigger AI Curation",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

### Option 2: Webhook-Based (Real-time)

For real-time updates, configure FreshRSS to send webhooks to n8n when new articles arrive (if FreshRSS supports it via extensions).

---

## Setting Up n8n Credentials

### 1. FreshRSS API Credential (HTTP Basic Auth)

In n8n:
1. Go to **Credentials** → **Add Credential**
2. Select **HTTP Basic Auth**
3. Name: `FreshRSS API`
4. User: `your-freshrss-username`
5. Password: `your-freshrss-api-password`

### 2. Django API Token (HTTP Header Auth)

In n8n:
1. Go to **Credentials** → **Add Credential**
2. Select **Header Auth**
3. Name: `Django API Token`
4. Header Name: `Authorization`
5. Header Value: `Token 1f3327082d4f3f086253001e7056c06915de23e2`

---

## Testing the Integration

### 1. Test Django API Manually

```bash
# Test stats endpoint
curl -H "Authorization: Token 1f3327082d4f3f086253001e7056c06915de23e2" \
  http://localhost:8000/api/stats/

# Test article ingestion
curl -X POST \
  -H "Authorization: Token 1f3327082d4f3f086253001e7056c06915de23e2" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Article",
    "link": "https://example.com/test",
    "description": "This is a test article",
    "source_name": "Test Source",
    "category_slug": "test"
  }' \
  http://localhost:8000/api/ingest/article/
```

### 2. Import Workflow to n8n

1. Copy the workflow JSON above
2. In n8n, click **Workflows** → **Import from File**
3. Paste the JSON
4. Update the URLs to match your servers
5. Add credentials
6. Activate the workflow

### 3. Manual Trigger

Click **Execute Workflow** to test immediately.

---

## Migrating Existing Sources to FreshRSS

### Export Current Sources

```bash
python manage.py shell
```

```python
from news.models import Source

for source in Source.objects.all():
    print(f"{source.name}: {source.url}")
```

### Import to FreshRSS

1. Go to FreshRSS → **Subscription Management**
2. Add each RSS feed manually, OR
3. Use OPML import (create OPML file from your sources)

---

## Monitoring

### Check n8n Logs
- Go to n8n workflow → **Executions**
- View success/failure of each run

### Check Django Logs
```bash
python manage.py runserver
```

### Check Sync Status
```bash
curl -H "Authorization: Token 1f3327082d4f3f086253001e7056c06915de23e2" \
  http://localhost:8000/api/stats/
```

---

## Troubleshooting

### Articles Not Appearing?

1. Check n8n execution logs
2. Verify FreshRSS API is accessible
3. Verify Django API is accessible from n8n
4. Check Django logs for errors
5. Verify authentication tokens are correct

### Duplicate Articles?

Articles are deduplicated by `guid` field. Ensure FreshRSS is providing unique GUIDs.

### AI Curation Not Running?

Trigger manually:
```bash
curl -X POST \
  -H "Authorization: Token 1f3327082d4f3f086253001e7056c06915de23e2" \
  http://localhost:8000/api/curate/
```

---

## Next Steps

After setting up the basic sync:

1. ✅ **Phase 1 Complete**: FreshRSS → Django sync working
2. **Phase 2**: Enhance AI scoring with user preferences
3. **Phase 3**: Add YouTube metadata extraction
4. **Phase 4**: Implement mood/context selector
5. **Phase 5**: Build personalization engine

---

## Advanced: Workflow Improvements

### Add Error Handling

Wrap HTTP requests in try-catch blocks in the Function node.

### Add Filtering

Filter out articles already in Django before sending (check by GUID).

### Batch Size Optimization

Adjust the `n` parameter in FreshRSS API call based on your needs.

### Schedule Optimization

- High-volume feeds: Every 30 minutes
- Low-volume feeds: Every 2-4 hours
- AI curation: Every 6-12 hours (to batch process)
