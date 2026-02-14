# Security & Code Review Fixes

Dit document behandelt alle bevindingen uit de code review en de status van de fixes.

---

## ✅ Opgelost (Completed)

### 1.2 Bare except clauses - **FIXED**

**Locaties:**
- `news/models.py` - get_interest_keywords(), get_category_weights(), get_source_weights()
- `news/ai_service.py` - classify_content_depth()
- `news/management/commands/curate_content.py` - reading context lookup

**Fix:**
```python
# Voor (gevaarlijk):
except:
    return []

# Na (veilig):
except (json.JSONDecodeError, TypeError, ValueError):
    return []
```

### 1.1 subprocess.run zonder URL validation - **FIXED**

**Locatie:** `news/media_service.py:17`

**Fix:**
```python
# URL scheme validation toegevoegd
parsed = urlparse(url)
if parsed.scheme not in ('http', 'https'):
    print(f"Invalid URL scheme for YouTube metadata: {parsed.scheme}")
    return None
```

---

## 🔧 Te Implementeren (To Do)

### 1.3 API Rate Limiting - **HOOG**

**Probleem:** API endpoints hebben geen rate limiting. Een aanvaller kan de server overbelasten.

**Fix:** Voeg toe aan `news_aggregator/settings.py`:

```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'rest_framework.authtoken',
    ...
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # NIEUW: Rate limiting
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/hour',      # Anonieme requests
        'user': '100/hour',     # Geauthenticeerde requests
    },
}
```

**Voor specifieke endpoints met dure operaties:**

```python
# news/api_views.py
from rest_framework.throttling import UserRateThrottle

class CurationThrottle(UserRateThrottle):
    rate = '10/hour'  # AI curation is duur, beperk tot 10/uur

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([CurationThrottle])  # NIEUW
def trigger_ai_curation(request):
    ...
```

### 1.4 Exception Leaking in API - **HOOG**

**Probleem:** `str(e)` wordt direct naar client gestuurd, kan interne info lekken.

**Locatie:** `news/api_views.py:158`

**Fix:**

```python
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_ai_curation(request):
    try:
        call_command('curate_content')
        return Response({
            'status': 'success',
            'message': 'AI curation started successfully'
        })
    except Exception as e:
        logger.exception("AI curation failed")  # Log met volledige stacktrace
        return Response({
            'status': 'error',
            'message': 'Curation failed. Please check server logs.'  # Generieke message
        }, status=500)
```

### 1.5 & 1.6 CDN Scripts zonder Integrity - **MEDIUM**

**Probleem:** Tailwind en HTMX laden van CDN zonder integrity hashes.

**Locatie:** `templates/base.html:21-24`

**Fix (voor development):**
```html
<!-- Gebruik integrity hashes -->
<script src="https://unpkg.com/htmx.org@1.9.10"
        integrity="sha384-D1Kt99CQMDuVetoL1lrYwg5t+9QdHe7NLX/SoJYkXDFfX37iInKRy5xLSi8nO7UC"
        crossorigin="anonymous"></script>
```

**Fix (voor productie - BETER):**

1. **Tailwind:** Gebruik build-stap in plaats van CDN:
```bash
npm install -D tailwindcss
npx tailwindcss init
```

`tailwind.config.js`:
```javascript
module.exports = {
  content: ["./templates/**/*.html"],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

`static/css/input.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Build command:
```bash
npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify
```

2. **HTMX:** Download en host lokaal:
```bash
curl -o static/js/htmx.min.js https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js
```

```html
<script src="{% static 'js/htmx.min.js' %}"></script>
```

---

## 📊 Data Model Fixes

### 2.1 Single-user Data Model - **ARCHITECTURAAL**

**Probleem:** `Article.is_read`, `is_saved`, `feedback_score` zijn niet per-user. Bij multi-user gebruik delen alle users dezelfde status.

**Status:** **Documentatie toegevoegd** (zie onder)

**Voor multi-user support (toekomstig):**

Maak tussentabel:
```python
class UserArticleStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    is_saved = models.BooleanField(default=False)
    feedback_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'article')
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'is_saved']),
        ]
```

Update views:
```python
# dashboard.py
all_articles = Article.objects.filter(
    userarticlestatus__user=request.user,
    userarticlestatus__is_read=False
)
```

**Huidige oplossing:** Gedocumenteerd als single-user app in README.

### 2.2 TextField voor JSON → JSONField - **MEDIUM**

**Probleem:** `interest_keywords`, `preferred_categories`, `preferred_sources` gebruiken TextField met handmatige JSON serialisatie.

**Fix:** Vervang in `news/models.py`:

```python
class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Voor (complex):
    # interest_keywords = models.TextField(default='[]')
    # def get_interest_keywords(self):
    #     try:
    #         return json.loads(self.interest_keywords)
    #     except (json.JSONDecodeError, TypeError, ValueError):
    #         return []

    # Na (simpel):
    interest_keywords = models.JSONField(default=list)
    preferred_categories = models.JSONField(default=dict)
    preferred_sources = models.JSONField(default=dict)

    # Geen getter/setter methods meer nodig!
```

**Migratie maken:**
```bash
python manage.py makemigrations
python manage.py migrate
```

**Update code die het gebruikt:**
```python
# Voor:
prefs.set_interest_keywords(['AI', 'tech'])
keywords = prefs.get_interest_keywords()

# Na:
prefs.interest_keywords = ['AI', 'tech']
keywords = prefs.interest_keywords  # Direct een list
```

---

## ⚡ Performance Fixes

### 4.1 N+1 Queries in update_from_feedback - **MEDIUM**

**Probleem:** Loopt over alle Categories en Sources met aparte queries.

**Locatie:** `news/models.py:136-156`

**Fix:**

```python
def update_from_feedback(self):
    """
    Analyzes user's feedback history and updates preferences.
    """
    from django.db.models import Count, Q, F

    # Get all liked/disliked articles in 2 queries
    liked_articles = Article.objects.filter(feedback_score=1)
    disliked_articles = Article.objects.filter(feedback_score=-1)

    # Update category preferences (1 query instead of N)
    category_stats = Category.objects.annotate(
        liked=Count('sources__articles', filter=Q(sources__articles__feedback_score=1)),
        disliked=Count('sources__articles', filter=Q(sources__articles__feedback_score=-1)),
        total=F('liked') + F('disliked')
    ).values('slug', 'liked', 'disliked', 'total')

    category_weights = {}
    for cat in category_stats:
        if cat['total'] > 0:
            weight = (cat['liked'] - cat['disliked']) / cat['total']
            category_weights[cat['slug']] = round(weight, 2)

    self.preferred_categories = category_weights  # Direct als JSONField

    # Similarly for sources (1 query instead of N)
    source_stats = Source.objects.annotate(
        liked=Count('articles', filter=Q(articles__feedback_score=1)),
        disliked=Count('articles', filter=Q(articles__feedback_score=-1)),
        total=F('liked') + F('disliked')
    ).values('id', 'liked', 'disliked', 'total')

    source_weights = {}
    for src in source_stats:
        if src['total'] > 0:
            weight = (src['liked'] - src['disliked']) / src['total']
            source_weights[str(src['id'])] = round(weight, 2)

    self.preferred_sources = source_weights  # Direct als JSONField

    # Extract keywords (unchanged)
    from collections import Counter
    words = Counter()
    for article in liked_articles[:50]:
        title_words = article.title.lower().split()
        words.update([w for w in title_words if len(w) > 4])

    self.interest_keywords = [word for word, count in words.most_common(20)]  # Direct als JSONField

    self.total_feedback_count = liked_articles.count() + disliked_articles.count()
    self.save()
```

### 4.2 recent_articles laadt volledige objecten - **MEDIUM**

**Probleem:** `Article.objects.all()[:200]` laadt alle velden terwijl alleen title nodig is.

**Locatie:** `news/management/commands/curate_content.py:101`

**Fix:**
```python
# Voor:
recent_articles = Article.objects.all()[:200]

# Na:
recent_articles = Article.objects.only('id', 'title')[:200]
# Of nog beter voor calculate_trend_score:
recent_titles = list(Article.objects.values_list('id', 'title')[:200])
```

### 4.3 article.save() in loop → bulk_update - **MEDIUM**

**Locatie:** `news/management/commands/curate_content.py`

**Fix:**
```python
# Voor (inefficiënt):
for article in unscored:
    if str(article.id) in scores:
        article.relevance_score = scores[str(article.id)]
    else:
        article.relevance_score = 50
    article.save()  # Aparte DB query per article!

# Na (efficiënt):
articles_to_update = []
for article in unscored:
    article.relevance_score = scores.get(str(article.id), 50)
    articles_to_update.append(article)

Article.objects.bulk_update(articles_to_update, ['relevance_score'])  # 1 query!
```

---

## 🐛 Robustness Fixes

### 5.2 ReadingContext weights > 1.0 - **MEDIUM**

**Probleem:** Weights tellen niet op tot 1.0, kan scores boven 100 geven.

**Fix 1: Validatie in model**

```python
# news/models.py
class ReadingContext(models.Model):
    ...
    relevance_weight = models.FloatField(default=0.6)
    personalization_weight = models.FloatField(default=0.3)
    serendipity_weight = models.FloatField(default=0.1)
    trend_weight = models.FloatField(default=0.2)

    def clean(self):
        """Validate that weights sum to ~1.0"""
        total = (
            self.relevance_weight +
            self.personalization_weight +
            self.serendipity_weight +
            self.trend_weight
        )
        if not (0.95 <= total <= 1.05):  # Allow small floating point errors
            raise ValidationError(
                f'Weights must sum to 1.0 (currently: {total:.2f}). '
                f'Adjust the weights so they add up to approximately 1.0.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()  # Trigger validation
        super().save(*args, **kwargs)
```

**Fix 2: Normalize in code**

```python
# news/ai_service.py - score_article_comprehensive()
def score_article_comprehensive(article, user_preferences=None, reading_context=None, recent_articles=None):
    ...

    if reading_context:
        # Normalize weights
        total_weight = (
            reading_context.relevance_weight +
            reading_context.personalization_weight +
            reading_context.serendipity_weight +
            reading_context.trend_weight
        )
        final_score = (
            (article.relevance_score * reading_context.relevance_weight +
             personalization * reading_context.personalization_weight +
             serendipity * reading_context.serendipity_weight +
             trend * reading_context.trend_weight) / total_weight  # Normalize!
        )
    else:
        ...

    return min(100, final_score)  # Cap at 100
```

**Fix 3: Update setup_contexts.py**

Fix de default weights in `news/management/commands/setup_contexts.py`:

```python
contexts = [
    {
        'name': 'Morning Briefing',
        'content_depth': 'light',
        'relevance_weight': 0.50,
        'personalization_weight': 0.30,
        'serendipity_weight': 0.05,
        'trend_weight': 0.15,  # Was 0.30, nu 0.15 zodat totaal = 1.0
    },
    ...
]
```

### 5.3 feedback_count % 10 is fragiel - **MEDIUM**

**Probleem:** Toggle van feedback kan count veranderen, waardoor update wordt overgeslagen of dubbel wordt getriggered.

**Locatie:** `news/views.py:230`

**Fix:**

```python
# news/models.py - Voeg veld toe
class UserPreference(models.Model):
    ...
    feedback_trigger_count = models.IntegerField(default=0)  # NIEUW

# news/views.py - Update logic
@login_required
@require_POST
def handle_feedback(request, article_id, action):
    ...
    article.save()

    # Update preferences periodically
    prefs, _ = UserPreference.objects.get_or_create(user=request.user)

    # Increment trigger count only on new feedback (niet bij toggle)
    old_score_was_neutral = Article.objects.get(id=article_id).feedback_score == 0  # Before update
    new_score_is_not_neutral = article.feedback_score != 0

    if old_score_was_neutral and new_score_is_not_neutral:
        prefs.feedback_trigger_count += 1
        prefs.save(update_fields=['feedback_trigger_count'])

        # Update every 10 NEW feedbacks
        if prefs.feedback_trigger_count % 10 == 0:
            prefs.update_from_feedback()
```

### 5.5 Geen validatie op action parameter - **MEDIUM**

**Locatie:** `news/views.py:213`

**Fix:**

```python
from django.http import HttpResponseBadRequest

@login_required
@require_POST
def handle_feedback(request, article_id, action):
    # Validatie toevoegen
    if action not in ('like', 'dislike'):
        return HttpResponseBadRequest("Invalid action. Must be 'like' or 'dislike'.")

    article = get_object_or_404(Article, pk=article_id)
    ...
```

### 5.6 Missing refresh_error.html - **LAAG**

**Probleem:** Template ontbreekt.

**Fix:** Maak `templates/components/refresh_error.html`:

```html
<div class="text-red-500 text-sm">
    ⚠️ Failed to refresh feeds. Please try again later.
</div>
```

---

## 📝 Code Quality Fixes

### 3.1 View Duplication - **MEDIUM**

**Probleem:** `dashboard()`, `category_detail()`, `saved_articles()` zijn bijna identiek.

**Fix:** Zie aparte sectie "View Refactoring" onderaan.

### 3.3 Dubbele format_duration - **LAAG**

**Probleem:** Functie bestaat in `media_service.py:152` en `templatetags/custom_filters.py:8`.

**Fix:**

```python
# news/templatetags/custom_filters.py
from news.media_service import format_duration as _format_duration

@register.filter(name='format_duration')
def format_duration(seconds):
    """Template filter wrapper for media_service.format_duration"""
    return _format_duration(seconds)
```

Verwijder de duplicate implementatie.

### 3.4 Dubbele {% load %} in card.html - **LAAG**

**Locatie:** Regel 1 én 39

**Fix:** Verwijder regel 39 (tweede {% load custom_filters %}).

### 3.5 Unused Imports - **LAAG**

**Fix:**

```python
# news/views.py - VERWIJDER:
from urllib.parse import quote  # Alleen gebruikt in export_obsidian
from django.db.models import Q    # Niet gebruikt

# news/models.py - VERWIJDER:
from django.db.models import Q, Avg  # Niet gebruikt
```

---

## 🔍 Logging

### 6.1 print() → logging - **MEDIUM**

**Probleem:** Hele codebase gebruikt `print()` voor errors.

**Fix:** Voeg logging toe aan `settings.py`:

```python
# news_aggregator/settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'news.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'news': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
```

**Update code:**

```python
# Aan begin van elk bestand:
import logging
logger = logging.getLogger(__name__)

# Vervang print() met logger:
# Voor:
print(f"Error extracting YouTube metadata: {e}")

# Na:
logger.error("Error extracting YouTube metadata", exc_info=True)
```

---

## 🔧 View Refactoring

### Refactored views.py (Elimineert 90+ regels duplicatie)

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import F
from django.http import HttpResponseBadRequest
import logging

from .models import Article, Category, Source, ReadingContext, UserPreference

logger = logging.getLogger(__name__)


def _article_list_view(request, queryset, page_title, extra_context=None):
    """
    Helper function for article list views (dashboard, category, saved).
    Reduces code duplication by ~90 lines.
    """
    categories = Category.objects.all()
    active_context = ReadingContext.objects.filter(
        user=request.user, is_active=True
    ).first()
    all_contexts = ReadingContext.objects.filter(user=request.user)

    # Sort by personalization score, then pub_date
    articles = queryset.select_related('source', 'source__category').order_by(
        F('personalization_score').desc(nulls_last=True),
        '-pub_date'
    )

    # Pagination
    paginator = Paginator(articles, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'categories': categories,
        'articles': page_obj,
        'page_title': page_title,
        'active_context': active_context,
        'all_contexts': all_contexts,
        **(extra_context or {}),
    }

    # HTMX support
    template = (
        'news/partials/article_list.html'
        if request.headers.get('HX-Request')
        else 'news/dashboard.html'
    )

    return render(request, template, context)


@login_required
def dashboard(request):
    """Main view: shows unread articles."""
    return _article_list_view(
        request,
        Article.objects.filter(is_read=False),
        'Dashboard'
    )


@login_required
def category_detail(request, slug):
    """Shows unread articles in a specific category."""
    category = get_object_or_404(Category, slug=slug)
    return _article_list_view(
        request,
        Article.objects.filter(source__category=category, is_read=False),
        category.name,
        {'current_category': category}
    )


@login_required
def saved_articles(request):
    """Shows all bookmarked articles."""
    return _article_list_view(
        request,
        Article.objects.filter(is_saved=True),
        'Saved Articles'
    )


@login_required
@require_POST
def handle_feedback(request, article_id, action):
    """Handle like/dislike feedback with validation."""
    # Validation
    if action not in ('like', 'dislike'):
        return HttpResponseBadRequest("Invalid action. Must be 'like' or 'dislike'.")

    article = get_object_or_404(Article, pk=article_id)

    score_map = {'like': 1, 'dislike': -1}
    new_score = score_map[action]

    # Toggle logic
    if article.feedback_score == new_score:
        article.feedback_score = 0
    else:
        article.feedback_score = new_score

    article.save()

    # Update user preferences periodically
    try:
        prefs, _ = UserPreference.objects.get_or_create(user=request.user)
        feedback_count = Article.objects.filter(feedback_score__in=[-1, 1]).count()

        if feedback_count % 10 == 0:
            prefs.update_from_feedback()
    except Exception:
        logger.exception("Error updating preferences after feedback")

    context = {'article': article}
    return render(request, 'components/feedback_buttons.html', context)


# ... rest of views remain unchanged
```

---

## 📋 Checklist voor Implementatie

### Prioriteit 1 (Direct implementeren):
- [x] 1.2 Bare except clauses fixed
- [x] 1.1 subprocess URL validation fixed
- [ ] 1.3 API rate limiting toevoegen
- [ ] 1.4 Exception leaking fixen
- [ ] 6.1 Logging implementeren (vervang print())

### Prioriteit 2 (Deze week):
- [ ] 2.2 JSONField migratie
- [ ] 5.2 ReadingContext weights validatie
- [ ] 5.5 Action parameter validatie
- [ ] 3.1 View refactoring
- [ ] 4.3 bulk_update implementeren

### Prioriteit 3 (Volgende sprint):
- [ ] 4.1 N+1 queries fixen
- [ ] 5.3 Feedback count fix
- [ ] 1.5/1.6 CDN → lokale assets
- [ ] 3.3-3.5 Code cleanup (duplicates, unused imports)

### Optioneel (Toekomstig):
- [ ] 2.1 Multi-user architecture (alleen als nodig)
- [ ] 7.2 Test suite schrijven
- [ ] 7.4 Tailwind build proces

---

## 📊 Impact Assessment

| Fix | Impact | Moeite | ROI |
|-----|--------|--------|-----|
| API rate limiting | Hoog | Klein | ⭐⭐⭐ |
| Exception leaking | Hoog | Klein | ⭐⭐⭐ |
| JSONField migratie | Medium | Medium | ⭐⭐ |
| View refactoring | Medium | Klein | ⭐⭐⭐ |
| Logging | Medium | Klein | ⭐⭐ |
| N+1 queries | Medium | Medium | ⭐⭐ |
| Weights validatie | Medium | Klein | ⭐⭐ |
| Bare excepts | Hoog | Klein | ⭐⭐⭐ (DONE) |

---

**Totaal geschatte tijd:**
- Prioriteit 1: 2-3 uur
- Prioriteit 2: 4-5 uur
- Prioriteit 3: 6-8 uur

**Totaal: ~12-16 uur werk** voor een production-ready applicatie.
