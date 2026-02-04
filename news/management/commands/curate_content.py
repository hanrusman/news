from django.core.management.base import BaseCommand
import time
from news.models import Article
from news.ai_service import summarize_article, score_relevance_batch

class Command(BaseCommand):
    help = 'Curates content using AI: scores relevance and summarizes long articles.'

    def handle(self, *args, **options):
        # 1. Summarize Long Articles without summary
        long_articles = Article.objects.filter(ai_summary__isnull=True).exclude(description='')[:20]
        self.stdout.write(f"Summarizing {long_articles.count()} articles...")
        
        for article in long_articles:
            if len(article.description) > 500: # Only summarize substantive ones
               summary = summarize_article(article.description)
               if summary:
                   article.ai_summary = summary
                   article.save()
                   self.stdout.write(f"  - Summarized: {article.title[:30]}...")
                   time.sleep(4) # Rate limit protection
        
        # 2. Score Relevance for unscored articles
        unscored = Article.objects.filter(relevance_score=0)[:50] # Batch of 50
        if unscored.exists():
            self.stdout.write(f"Scoring {unscored.count()} articles...")
            batch_data = [{'id': a.id, 'title': a.title, 'description': a.description} for a in unscored]
            
            scores = score_relevance_batch(batch_data)
            
            for article in unscored:
                if str(article.id) in scores:
                    article.relevance_score = scores[str(article.id)]
                else:
                    article.relevance_score = 50 # Default if AI misses it
                article.save()
            
            self.stdout.write(self.style.SUCCESS("Scoring complete."))
