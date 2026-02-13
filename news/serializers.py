from rest_framework import serializers
from .models import Article, Source, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class SourceSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_slug = serializers.SlugField(write_only=True, required=False)

    class Meta:
        model = Source
        fields = ['id', 'name', 'url', 'source_type', 'category', 'category_slug', 'icon_url']

    def create(self, validated_data):
        category_slug = validated_data.pop('category_slug', None)
        if category_slug:
            category, _ = Category.objects.get_or_create(
                slug=category_slug,
                defaults={'name': category_slug.replace('-', ' ').title()}
            )
            validated_data['category'] = category
        return super().create(validated_data)

class ArticleIngestSerializer(serializers.Serializer):
    """
    Serializer for ingesting articles from FreshRSS via n8n.
    Accepts flexible field names from FreshRSS.
    """
    # Required fields
    title = serializers.CharField(max_length=500)
    link = serializers.URLField(max_length=500)

    # Optional fields
    description = serializers.CharField(required=False, allow_blank=True, default='')
    content = serializers.CharField(required=False, allow_blank=True)
    pub_date = serializers.DateTimeField(required=False)
    published = serializers.DateTimeField(required=False)
    guid = serializers.CharField(max_length=500, required=False)
    id = serializers.CharField(max_length=500, required=False)
    image_url = serializers.URLField(max_length=1000, required=False, allow_blank=True)
    thumbnail = serializers.URLField(max_length=1000, required=False, allow_blank=True)

    # Source information
    source_name = serializers.CharField(max_length=200, required=False)
    source_url = serializers.URLField(required=False)
    source_type = serializers.ChoiceField(
        choices=['rss', 'yt', 'podcast'],
        required=False,
        default='rss'
    )
    category_slug = serializers.SlugField(required=False)

    def validate(self, data):
        """
        Normalize fields from FreshRSS format.
        """
        # Use content as description if description is empty
        if not data.get('description') and data.get('content'):
            data['description'] = data['content']

        # Use 'published' as pub_date if pub_date not provided
        if not data.get('pub_date') and data.get('published'):
            data['pub_date'] = data['published']

        # Use 'id' as guid if guid not provided
        if not data.get('guid') and data.get('id'):
            data['guid'] = data['id']

        # Use link as guid if no guid
        if not data.get('guid'):
            data['guid'] = data['link']

        # Use thumbnail as image_url if image_url not provided
        if not data.get('image_url') and data.get('thumbnail'):
            data['image_url'] = data['thumbnail']

        return data

    def create(self, validated_data):
        """
        Create or update article with associated source.
        Auto-enriches YouTube/podcast articles with metadata.
        """
        from django.utils import timezone
        from news.media_service import enrich_article_with_metadata

        # Extract source info
        source_name = validated_data.pop('source_name', 'Unknown Source')
        source_url = validated_data.pop('source_url', validated_data['link'])
        source_type = validated_data.pop('source_type', 'rss')
        category_slug = validated_data.pop('category_slug', 'general')

        # Remove extra fields not in Article model
        validated_data.pop('content', None)
        validated_data.pop('published', None)
        validated_data.pop('id', None)
        validated_data.pop('thumbnail', None)

        # Get or create category
        category, _ = Category.objects.get_or_create(
            slug=category_slug,
            defaults={'name': category_slug.replace('-', ' ').title()}
        )

        # Get or create source
        source, _ = Source.objects.get_or_create(
            url=source_url,
            defaults={
                'name': source_name,
                'source_type': source_type,
                'category': category
            }
        )

        # Set default pub_date if not provided
        if not validated_data.get('pub_date'):
            validated_data['pub_date'] = timezone.now()

        # Create or update article
        article, created = Article.objects.update_or_create(
            guid=validated_data['guid'],
            defaults={
                **validated_data,
                'source': source
            }
        )

        # Auto-enrich YouTube/Podcast articles with metadata
        if source_type in ['yt', 'podcast'] and created:
            try:
                enrich_article_with_metadata(article)
            except Exception as e:
                # Don't fail ingestion if enrichment fails
                print(f"Warning: Could not enrich article {article.id}: {e}")

        return article

class ArticleSerializer(serializers.ModelSerializer):
    source = SourceSerializer(read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'source', 'title', 'link', 'description',
            'pub_date', 'image_url', 'ai_summary', 'relevance_score',
            'is_read', 'is_saved', 'feedback_score', 'created_at'
        ]
