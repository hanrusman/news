from django.db import models

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

    # Status
    is_read = models.BooleanField(default=False)
    is_saved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.title
