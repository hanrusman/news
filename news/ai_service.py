import os
import google.generativeai as genai
from django.conf import settings
import json
from collections import Counter

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-2.0-flash')

def summarize_article(text):
    """
    Summarizes the given text using Gemini.
    """
    if not text or len(text) < 300:
        return None
        
    try:
        prompt = f"Summarize the following news article in 3-4 bullet points. Keep it concise:\n\n{text[:10000]}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error summarizing: {e}")
        return None

def score_relevance_batch(articles_data, user_preferences=None):
    """
    Scores a batch of articles based on relevance + user preferences.
    articles_data: list of dicts {'id': int, 'title': str, 'description': str, 'category': str}
    user_preferences: UserPreference model instance (optional)
    Returns: dict mapping article_id -> score (int)
    """
    if not articles_data:
        return {}

    # Build interest profile from user preferences
    interest_profile = "a tech-savvy user interested in AI, World News, and Tech"
    if user_preferences:
        keywords = user_preferences.get_interest_keywords()
        if keywords:
            interest_profile = f"a user interested in: {', '.join(keywords[:10])}"

    # Prepare prompt
    candidates = ""
    for a in articles_data:
        category_info = f"Category: {a.get('category', 'general')}\n" if 'category' in a else ""
        candidates += f"ID: {a['id']}\n{category_info}Title: {a['title']}\nSnippet: {a['description'][:200]}\n---\n"

    prompt = f"""
    You are a personal news curator. Rate the following articles on a scale of 0-100 based on how interesting they likely are to {interest_profile}.

    Consider:
    - Relevance to user interests
    - Article quality and depth
    - Uniqueness and novelty

    Return ONLY a JSON object mapping IDs to scores. Example: {{"123": 80, "124": 20}}

    Articles:
    {candidates}
    """

    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        print(f"Error scoring: {e}")
        return {}


def calculate_personalization_score(article, user_preferences):
    """
    Calculate personalized score based on user's historical preferences.
    Returns: float 0-100
    """
    if not user_preferences:
        return 50.0  # Neutral score

    score = 50.0  # Start neutral

    # Category preference boost/penalty
    category_weights = user_preferences.get_category_weights()
    category_slug = article.source.category.slug if article.source and article.source.category else None
    if category_slug and category_slug in category_weights:
        # Weight is between -1 and 1, scale to -20 to +20
        score += category_weights[category_slug] * 20

    # Source preference boost/penalty
    source_weights = user_preferences.get_source_weights()
    source_id = str(article.source.id) if article.source else None
    if source_id and source_id in source_weights:
        score += source_weights[source_id] * 15

    # Keyword matching boost
    keywords = user_preferences.get_interest_keywords()
    if keywords:
        title_lower = article.title.lower()
        desc_lower = (article.description or '').lower()
        matches = sum(1 for kw in keywords if kw.lower() in title_lower or kw.lower() in desc_lower)
        score += min(matches * 5, 20)  # Cap at +20

    # Content depth matching
    if user_preferences.preferred_content_depth == article.content_depth:
        score += 10
    elif (user_preferences.preferred_content_depth == 'light' and article.content_depth == 'heavy') or \
         (user_preferences.preferred_content_depth == 'heavy' and article.content_depth == 'light'):
        score -= 10

    # Clamp to 0-100
    return max(0, min(100, score))


def calculate_trend_score(article, recent_articles=None):
    """
    Calculate trend score based on topic popularity.
    Returns: float 0-100
    """
    # Simplified version: uses category and keyword frequency
    # In production, you'd analyze trending topics across sources

    if not recent_articles:
        return 50.0  # Neutral

    # Extract keywords from article
    title_words = set(article.title.lower().split())
    title_words = {w for w in title_words if len(w) > 4}  # Filter short words

    # Count occurrences in recent articles
    word_counts = Counter()
    for other in recent_articles[:100]:  # Sample recent articles
        if other.id == article.id:
            continue
        other_words = set(other.title.lower().split())
        matches = title_words & other_words
        word_counts.update(matches)

    # Score based on trending keywords
    if not word_counts:
        return 30.0  # Less trendy if no matches

    # More matches = more trending
    total_matches = sum(word_counts.values())
    score = min(50 + (total_matches * 5), 100)  # Scale and cap

    return score


def calculate_serendipity_score(article, user_preferences):
    """
    Calculate serendipity score - how unexpected but potentially interesting.
    Returns: float 0-100
    """
    if not user_preferences:
        return 50.0

    score = 50.0

    # Articles from unfamiliar categories get higher serendipity
    category_weights = user_preferences.get_category_weights()
    category_slug = article.source.category.slug if article.source and article.source.category else None

    if category_slug:
        if category_slug not in category_weights:
            score += 30  # Unexplored category
        elif category_weights[category_slug] < 0:
            score += 20  # Previously disliked category (might change mind)
        else:
            score -= 20  # Familiar territory

    # Articles with no keyword matches are more serendipitous
    keywords = user_preferences.get_interest_keywords()
    if keywords:
        title_lower = article.title.lower()
        matches = sum(1 for kw in keywords if kw.lower() in title_lower)
        score -= matches * 5  # Fewer matches = more serendipitous

    return max(0, min(100, score))


def classify_content_depth(article):
    """
    Classify article content depth using AI.
    Returns: 'light', 'medium', or 'heavy'
    """
    text_length = len(article.description or '')

    # Simple heuristic first (saves API calls)
    if text_length < 500:
        return 'light'
    elif text_length > 2000:
        return 'heavy'

    # Use AI for medium-length content
    try:
        prompt = f"""
        Classify this article as 'light', 'medium', or 'heavy' based on content depth:

        Title: {article.title}
        Snippet: {article.description[:500]}

        Light: Quick news, short updates, breaking news
        Medium: Standard news article with some detail
        Heavy: In-depth analysis, long-form journalism, detailed investigation

        Return ONLY one word: light, medium, or heavy
        """

        response = model.generate_content(prompt)
        classification = response.text.strip().lower()

        if classification in ['light', 'medium', 'heavy']:
            return classification
    except:
        pass

    return 'medium'  # Default


def score_article_comprehensive(article, user_preferences=None, reading_context=None, recent_articles=None):
    """
    Comprehensive scoring that combines all factors.
    Updates article with all score fields.
    """
    # Calculate individual scores
    personalization = calculate_personalization_score(article, user_preferences)
    trend = calculate_trend_score(article, recent_articles)
    serendipity = calculate_serendipity_score(article, user_preferences)

    # Store individual scores
    article.personalization_score = personalization
    article.trend_score = trend
    article.serendipity_score = serendipity

    # Classify content depth if not set
    if not article.content_depth or article.content_depth == 'medium':
        article.content_depth = classify_content_depth(article)

    # Calculate final score based on reading context weights
    if reading_context:
        final_score = (
            article.relevance_score * reading_context.relevance_weight +
            personalization * reading_context.personalization_weight +
            serendipity * reading_context.serendipity_weight +
            trend * reading_context.trend_weight
        )
    else:
        # Default weights if no context
        final_score = (
            article.relevance_score * 0.4 +
            personalization * 0.3 +
            serendipity * 0.1 +
            trend * 0.2
        )

    return final_score
