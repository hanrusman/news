from django.contrib import admin
from .models import Category, Source, Article

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
    list_display = ('title', 'source', 'pub_date', 'is_read', 'is_saved')
    list_filter = ('is_read', 'is_saved', 'source__category', 'pub_date')
    search_fields = ('title', 'description')
