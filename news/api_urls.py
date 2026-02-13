from django.urls import path
from . import api_views

app_name = 'api'

urlpatterns = [
    # Article ingestion
    path('ingest/article/', api_views.ingest_article, name='ingest_article'),
    path('ingest/articles/', api_views.ingest_articles_batch, name='ingest_articles_batch'),

    # AI curation
    path('curate/', api_views.trigger_ai_curation, name='trigger_curation'),

    # Info endpoints
    path('stats/', api_views.api_stats, name='stats'),
    path('sources/', api_views.list_sources, name='list_sources'),
]
