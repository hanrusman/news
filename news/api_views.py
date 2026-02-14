from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.conf import settings
from .models import Article, Source
from .serializers import ArticleIngestSerializer, ArticleSerializer, SourceSerializer
from .throttles import IngestThrottle, CurationThrottle
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([IngestThrottle])
def ingest_article(request):
    """
    API endpoint to ingest a single article from FreshRSS.

    POST /api/ingest/article/
    Headers:
        Authorization: Token <your-token>
    Body:
        {
            "title": "Article Title",
            "link": "https://...",
            "description": "Article content...",
            "pub_date": "2024-01-01T00:00:00Z",
            "guid": "unique-id",
            "source_name": "TechCrunch",
            "source_url": "https://techcrunch.com/feed",
            "category_slug": "tech",
            "image_url": "https://..."
        }
    """
    serializer = ArticleIngestSerializer(data=request.data)

    if serializer.is_valid():
        article = serializer.save()
        response_serializer = ArticleSerializer(article)
        return Response(
            {
                'status': 'success',
                'message': 'Article ingested successfully',
                'article': response_serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    return Response(
        {
            'status': 'error',
            'message': 'Invalid data',
            'errors': serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([IngestThrottle])
def ingest_articles_batch(request):
    """
    API endpoint to ingest multiple articles in batch from FreshRSS.

    POST /api/ingest/articles/
    Headers:
        Authorization: Token <your-token>
    Body:
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
    """
    articles_data = request.data.get('articles', [])

    if not articles_data:
        return Response(
            {
                'status': 'error',
                'message': 'No articles provided'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    created_articles = []
    errors = []

    for article_data in articles_data:
        serializer = ArticleIngestSerializer(data=article_data)
        if serializer.is_valid():
            try:
                article = serializer.save()
                created_articles.append(article.id)
            except Exception as e:
                # Log the full error server-side
                logger.error(f"Failed to save article '{article_data.get('title', 'Unknown')}': {e}", exc_info=True)
                # Return generic error to client (don't leak exception details)
                errors.append({
                    'article': article_data.get('title', 'Unknown'),
                    'error': 'Failed to save article'
                })
        else:
            errors.append({
                'article': article_data.get('title', 'Unknown'),
                'error': serializer.errors
            })

    return Response(
        {
            'status': 'success',
            'message': f'Processed {len(articles_data)} articles',
            'created': len(created_articles),
            'errors': len(errors),
            'created_ids': created_articles,
            'error_details': errors
        },
        status=status.HTTP_201_CREATED
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_stats(request):
    """
    Get API statistics.

    GET /api/stats/
    """
    return Response({
        'total_articles': Article.objects.count(),
        'unread_articles': Article.objects.filter(is_read=False).count(),
        'saved_articles': Article.objects.filter(is_saved=True).count(),
        'total_sources': Source.objects.count(),
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([CurationThrottle])
def trigger_ai_curation(request):
    """
    Trigger AI curation process manually.

    Rate limited to 10 requests per hour due to expensive AI operations.

    POST /api/curate/
    """
    from django.core.management import call_command

    try:
        # Run curation in background (for production, use Celery)
        call_command('curate_content')
        return Response({
            'status': 'success',
            'message': 'AI curation triggered successfully'
        })
    except Exception as e:
        # Log the full error server-side
        logger.error(f"AI curation failed: {e}", exc_info=True)
        # Return generic error to client (don't leak exception details)
        return Response({
            'status': 'error',
            'message': 'AI curation failed. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_sources(request):
    """
    List all sources.

    GET /api/sources/
    """
    sources = Source.objects.all()
    serializer = SourceSerializer(sources, many=True)
    return Response({
        'status': 'success',
        'count': sources.count(),
        'sources': serializer.data
    })
