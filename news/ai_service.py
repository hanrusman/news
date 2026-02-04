import os
import google.generativeai as genai
from django.conf import settings

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

def score_relevance_batch(articles_data):
    """
    Scores a batch of articles based on relevance.
    articles_data: list of dicts {'id': int, 'title': str, 'description': str}
    Returns: dict mapping article_id -> score (int)
    """
    if not articles_data:
        return {}

    # Prepare prompt
    candidates = ""
    for a in articles_data:
        candidates += f"ID: {a['id']}\nTitle: {a['title']}\nSnippet: {a['description'][:200]}\n---\n"

    prompt = f"""
    You are a personal news curator. Rate the following articles on a scale of 0-100 based on how interesting they likely are to a tech-savvy user interested in AI, World News, and Tech.
    
    Return ONLY a JSON object mapping IDs to scores. Example: {{"123": 80, "124": 20}}

    Articles:
    {candidates}
    """
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        import json
        return json.loads(response.text)
    except Exception as e:
        print(f"Error scoring: {e}")
        return {}
