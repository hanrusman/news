from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from urllib.parse import quote
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Article, Category, Source

@login_required
def dashboard(request):
    """
    Main view: shows unread articles and sidebar categories.
    """
    categories = Category.objects.all()
    # Get unread articles, sorted by date
    all_articles = Article.objects.filter(is_read=False).select_related('source', 'source__category')
    
    # Pagination (20 per page)
    paginator = Paginator(all_articles, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'categories': categories,
        'articles': page_obj, # This is now the page object
        'page_title': 'Dashboard'
    }
    
    if request.headers.get('HX-Request'):
        # If HTMX request (scrolling), return just the rows
        return render(request, 'news/partials/article_list.html', context)
        
    return render(request, 'news/dashboard.html', context)

@login_required
def category_detail(request, slug):
    categories = Category.objects.all()
    category = get_object_or_404(Category, slug=slug)
    all_articles = Article.objects.filter(source__category=category, is_read=False).select_related('source')
    
    paginator = Paginator(all_articles, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'current_category': category,
        'articles': page_obj,
        'page_title': category.name
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'news/partials/article_list.html', context)

    return render(request, 'news/dashboard.html', context)

@login_required
def saved_articles(request):
    """
    Shows all bookmarked articles.
    """
    categories = Category.objects.all()
    all_articles = Article.objects.filter(is_saved=True).select_related('source', 'source__category')
    
    paginator = Paginator(all_articles, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'categories': categories,
        'articles': page_obj,
        'page_title': 'Saved Articles'
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'news/partials/article_list.html', context)

    return render(request, 'news/dashboard.html', context)

@login_required
@require_POST
def mark_read(request, article_id):
    """
    HTMX endpoint to mark an article as read.
    """
    article = get_object_or_404(Article, pk=article_id)
    article.is_read = True
    article.save()
    # Return empty response or checkmark
    return render(request, 'components/mark_read_success.html')

@login_required
@require_POST
def toggle_bookmark(request, article_id):
    """
    Toggles the internal bookmark state.
    """
    article = get_object_or_404(Article, pk=article_id)
    article.is_saved = not article.is_saved
    article.save()
    
    # Return button state
    context = {'article': article}
    # We return the "bookmark success" button if saved, or the normal button (rendered inline) if unsaved. 
    # For simplicity in this HTMX flow, we return a simpler component that just looks like the active state,
    # or re-render the button. Ideally we'd re-render the whole button snippet.
    # But since we have bookmark_success.html:
    if article.is_saved:
        return render(request, 'components/bookmark_success.html', context)
    else:
        # Return the original grey button state (hardcoded for speed here, or use a template partial)
        return render(request, 'components/bookmark_inactive.html', context)

@login_required
@require_POST
def export_obsidian(request, article_id):
    """
    Returns Obsidian URI to create a note.
    """
    article = get_object_or_404(Article, pk=article_id)
    
    # Construct Obsidian URI
    content = f"{article.link}\n\n{article.description}\n\nAI Summary:\n{article.ai_summary or 'No summary available.'}"
    obsidian_uri = f"obsidian://new?name={quote(article.title)}&content={quote(content)}"
    
    context = {
        'article': article,
        'obsidian_uri': obsidian_uri
    }
    return render(request, 'components/obsidian_success.html', context)

@login_required
@require_POST
def refresh_feeds(request):
    """
    Triggers the fetch_feeds command and returns a success status.
    """
    from django.core.management import call_command
    try:
        call_command('fetch_feeds')
        return render(request, 'components/refresh_success.html') # We'll create this or just return 200
    except Exception as e:
        # In a real app we'd log this
        print(f"Error fetching feeds: {e}")
        return render(request, 'components/refresh_error.html', status=500)

@login_required
@require_POST
def handle_feedback(request, article_id, action):
    """
    Handle like/dislike feedback. Action key: 'like' (1) or 'dislike' (-1).
    Toggles the score if already selected.
    """
    article = get_object_or_404(Article, pk=article_id)
    
    score_map = {'like': 1, 'dislike': -1}
    new_score = score_map.get(action, 0)
    
    # Toggle logic: if clicking "like" and it's already liked, reset to 0
    if article.feedback_score == new_score:
        article.feedback_score = 0
    else:
        article.feedback_score = new_score
        
    article.save()
    
    # Return the updated buttons
    context = {'article': article}
    return render(request, 'components/feedback_buttons.html', context)
