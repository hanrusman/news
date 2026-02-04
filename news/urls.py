from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('saved/', views.saved_articles, name='saved_articles'),
    path('refresh/', views.refresh_feeds, name='refresh_feeds'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('article/<int:article_id>/read/', views.mark_read, name='mark_read'),
    path('article/<int:article_id>/bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    path('article/<int:article_id>/feedback/<str:action>/', views.handle_feedback, name='handle_feedback'),
    path('article/<int:article_id>/export-obsidian/', views.export_obsidian, name='export_obsidian'),
]
