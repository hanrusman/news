from django.contrib import admin
from .models import Category, Source, Article, UserPreference, ReadingContext

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type', 'category', 'url')
    list_filter = ('source_type', 'category')
    search_fields = ('name', 'url')

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'pub_date', 'relevance_score', 'personalization_score', 'is_read', 'is_saved', 'feedback_score')
    list_filter = ('is_read', 'is_saved', 'source__category', 'source__source_type', 'content_depth', 'pub_date')
    search_fields = ('title', 'description', 'author')
    readonly_fields = ('created_at', 'relevance_score', 'personalization_score', 'trend_score', 'serendipity_score')

    fieldsets = (
        ('Basic Info', {
            'fields': ('source', 'title', 'link', 'description', 'pub_date', 'guid', 'image_url')
        }),
        ('AI Scoring', {
            'fields': ('ai_summary', 'relevance_score', 'personalization_score', 'trend_score', 'serendipity_score', 'content_depth')
        }),
        ('Media Metadata', {
            'fields': ('duration_seconds', 'author', 'view_count'),
            'classes': ('collapse',),
        }),
        ('User Interaction', {
            'fields': ('is_read', 'is_saved', 'feedback_score', 'created_at')
        }),
    )

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'preferred_content_depth', 'total_feedback_count', 'last_updated')
    readonly_fields = ('interest_keywords', 'preferred_categories', 'preferred_sources', 'total_feedback_count', 'last_updated')

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Learned Preferences (Read-only)', {
            'fields': ('interest_keywords', 'preferred_categories', 'preferred_sources', 'total_feedback_count', 'last_updated'),
            'description': 'These are automatically learned from user feedback. Run curate_content --update-preferences to refresh.'
        }),
        ('Manual Settings', {
            'fields': ('preferred_content_depth', 'current_mood')
        }),
    )

@admin.register(ReadingContext)
class ReadingContextAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'content_depth', 'is_active')
    list_filter = ('user', 'is_active', 'content_depth')
    filter_horizontal = ('enabled_categories',)

    fieldsets = (
        ('Basic', {
            'fields': ('user', 'name', 'is_active')
        }),
        ('Content Filters', {
            'fields': ('enabled_categories', 'content_depth')
        }),
        ('Scoring Weights', {
            'fields': ('relevance_weight', 'personalization_weight', 'serendipity_weight', 'trend_weight'),
            'description': 'Weights should add up to ~1.0 for balanced scoring.'
        }),
    )
