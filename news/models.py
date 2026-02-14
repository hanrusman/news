from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q, Avg
import json

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Source(models.Model):
    SOURCE_TYPES = [
        ('rss', 'RSS Feed'),
        ('yt', 'YouTube Channel'),
        ('podcast', 'Podcast'),
    ]

    name = models.CharField(max_length=200)
    url = models.URLField(help_text="RSS Feed URL")
    source_type = models.CharField(max_length=10, choices=SOURCE_TYPES, default='rss')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='sources')
    icon_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class Article(models.Model):
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=500)
    link = models.URLField(max_length=500, unique=True)
    description = models.TextField(blank=True)
    pub_date = models.DateTimeField()
    guid = models.CharField(max_length=500, unique=True, null=True, blank=True)
    image_url = models.URLField(max_length=1000, blank=True, null=True)

    # AI Content
    ai_summary = models.TextField(blank=True, null=True)
    relevance_score = models.IntegerField(default=0, help_text="0-100 score based on user interests")
    personalization_score = models.FloatField(default=0.0, help_text="Personalized score combining AI + user preferences")
    trend_score = models.FloatField(default=0.0, help_text="Market trend/importance score")
    serendipity_score = models.FloatField(default=0.0, help_text="Score for unexpected but potentially interesting content")

    # Status
    is_read = models.BooleanField(default=False)
    is_saved = models.BooleanField(default=False)
    feedback_score = models.IntegerField(default=0) # -1: Dislike, 0: Neutral, 1: Like
    created_at = models.DateTimeField(auto_now_add=True)

    # Metadata for YouTube/Podcasts
    duration_seconds = models.IntegerField(null=True, blank=True, help_text="Video/podcast duration")
    author = models.CharField(max_length=200, blank=True, help_text="Channel/Podcast author")
    view_count = models.IntegerField(null=True, blank=True)

    # Content classification
    content_depth = models.CharField(max_length=20, choices=[
        ('light', 'Light/Quick Read'),
        ('medium', 'Medium Depth'),
        ('heavy', 'Deep/Long-form')
    ], default='medium')

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.title


class UserPreference(models.Model):
    """
    Stores learned preferences for a user based on their feedback.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')

    # Learned interests (stored as JSON)
    interest_keywords = models.JSONField(default=list, help_text="List of interest keywords")
    preferred_categories = models.JSONField(default=dict, help_text="Dict of category_slug -> weight")
    preferred_sources = models.JSONField(default=dict, help_text="Dict of source_id -> weight")

    # Content preferences
    preferred_content_depth = models.CharField(max_length=20, choices=[
        ('light', 'Prefer Light Content'),
        ('medium', 'Balanced'),
        ('heavy', 'Prefer Deep Dives')
    ], default='medium')

    # Current mood/context (can be updated dynamically)
    current_mood = models.CharField(max_length=50, default='balanced', help_text="Current reading mood")

    # Learning metadata
    total_feedback_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)


    def update_from_feedback(self):
        """
        Analyzes user's feedback history and updates preferences.
        Called periodically or after N feedbacks.
        """
        from django.db.models import Count, Q

        # Get all user's articles with feedback
        liked_articles = Article.objects.filter(feedback_score=1)
        disliked_articles = Article.objects.filter(feedback_score=-1)

        # Update category preferences
        category_weights = {}
        for cat in Category.objects.all():
            liked_count = liked_articles.filter(source__category=cat).count()
            disliked_count = disliked_articles.filter(source__category=cat).count()
            total = liked_count + disliked_count
            if total > 0:
                # Weight between -1 and 1
                weight = (liked_count - disliked_count) / total
                category_weights[cat.slug] = round(weight, 2)

        self.preferred_categories = category_weights

        # Update source preferences
        source_weights = {}
        for source in Source.objects.all():
            liked_count = liked_articles.filter(source=source).count()
            disliked_count = disliked_articles.filter(source=source).count()
            total = liked_count + disliked_count
            if total > 0:
                weight = (liked_count - disliked_count) / total
                source_weights[str(source.id)] = round(weight, 2)

        self.preferred_sources = source_weights

        # Extract keywords from liked articles (simple version)
        # In production, you'd use NLP/TF-IDF
        from collections import Counter
        words = Counter()
        for article in liked_articles[:50]:  # Sample recent likes
            title_words = article.title.lower().split()
            words.update([w for w in title_words if len(w) > 4])  # Filter short words

        # Top 20 keywords
        top_keywords = [word for word, count in words.most_common(20)]
        self.interest_keywords = top_keywords

        self.total_feedback_count = liked_articles.count() + disliked_articles.count()
        self.save()

    def __str__(self):
        return f"Preferences for {self.user.username}"


class ReadingContext(models.Model):
    """
    Stores different reading contexts/moods that user can switch between.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contexts')
    name = models.CharField(max_length=100, help_text="e.g., 'Morning Briefing', 'Deep Dive', 'Light Reading'")

    # Category filters
    enabled_categories = models.ManyToManyField(Category, blank=True)

    # Content depth preference for this context
    content_depth = models.CharField(max_length=20, choices=[
        ('light', 'Light Content Only'),
        ('medium', 'Mixed'),
        ('heavy', 'Deep Content Only')
    ], default='medium')

    # Scoring weights for this context (must sum to 1.0)
    relevance_weight = models.FloatField(default=0.5, help_text="Weight for AI relevance score")
    personalization_weight = models.FloatField(default=0.3, help_text="Weight for personalization")
    serendipity_weight = models.FloatField(default=0.05, help_text="Weight for serendipity")
    trend_weight = models.FloatField(default=0.15, help_text="Weight for trending topics")

    is_active = models.BooleanField(default=False)

    def clean(self):
        """Validate that scoring weights sum to approximately 1.0"""
        from django.core.exceptions import ValidationError

        total_weight = (
            self.relevance_weight +
            self.personalization_weight +
            self.serendipity_weight +
            self.trend_weight
        )

        # Allow small floating point errors (within 0.01)
        if abs(total_weight - 1.0) > 0.01:
            raise ValidationError({
                'relevance_weight': f'Scoring weights must sum to 1.0 (currently {total_weight:.2f})',
                'personalization_weight': f'Scoring weights must sum to 1.0 (currently {total_weight:.2f})',
                'serendipity_weight': f'Scoring weights must sum to 1.0 (currently {total_weight:.2f})',
                'trend_weight': f'Scoring weights must sum to 1.0 (currently {total_weight:.2f})',
            })

    def save(self, *args, **kwargs):
        """Override save to call clean() for validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.name}"
