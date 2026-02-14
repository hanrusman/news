from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import time
from news.models import Article, UserPreference, ReadingContext
from news.ai_service import (
    summarize_article,
    score_relevance_batch,
    score_article_comprehensive,
    classify_content_depth
)

class Command(BaseCommand):
    help = 'Curates content using AI: scores relevance, personalizes, and summarizes articles.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-preferences',
            action='store_true',
            help='Update user preferences from feedback history',
        )

    def handle(self, *args, **options):
        # Get or create user preferences (assuming single user for now)
        try:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.WARNING("No users found. Create a superuser first."))
                return

            user_prefs, created = UserPreference.objects.get_or_create(user=user)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created preferences for {user.username}"))

            # Update preferences from feedback if requested
            if options['update_preferences']:
                self.stdout.write("Updating user preferences from feedback history...")
                user_prefs.update_from_feedback()
                self.stdout.write(self.style.SUCCESS(
                    f"Updated preferences: {len(user_prefs.interest_keywords)} keywords, "
                    f"{len(user_prefs.preferred_categories)} category weights"
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading preferences: {e}"))
            user_prefs = None

        # Get active reading context
        try:
            reading_context = ReadingContext.objects.filter(user=user, is_active=True).first()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not load reading context: {e}"))
            reading_context = None

        # 1. Summarize Long Articles without summary
        long_articles = Article.objects.filter(ai_summary__isnull=True).exclude(description='')[:20]
        self.stdout.write(f"\n[1/4] Summarizing {long_articles.count()} articles...")

        for article in long_articles:
            if len(article.description) > 500:  # Only summarize substantive ones
                summary = summarize_article(article.description)
                if summary:
                    article.ai_summary = summary
                    article.save()
                    self.stdout.write(f"  ✓ Summarized: {article.title[:50]}...")
                    time.sleep(4)  # Rate limit protection

        # 2. Score Relevance for unscored articles (AI scoring)
        unscored = Article.objects.filter(relevance_score=0)[:50]  # Batch of 50
        if unscored.exists():
            self.stdout.write(f"\n[2/4] AI scoring {unscored.count()} articles...")
            batch_data = [
                {
                    'id': a.id,
                    'title': a.title,
                    'description': a.description,
                    'category': a.source.category.name if a.source and a.source.category else 'general'
                }
                for a in unscored
            ]

            scores = score_relevance_batch(batch_data, user_prefs)

            for article in unscored:
                if str(article.id) in scores:
                    article.relevance_score = scores[str(article.id)]
                else:
                    article.relevance_score = 50  # Default if AI misses it
                article.save()

            self.stdout.write(self.style.SUCCESS("  ✓ AI scoring complete"))

        # 3. Classify content depth for articles
        unclassified = Article.objects.filter(content_depth='medium')[:50]
        if unclassified.exists():
            self.stdout.write(f"\n[3/4] Classifying content depth for {unclassified.count()} articles...")
            for article in unclassified:
                article.content_depth = classify_content_depth(article)
                article.save()
            self.stdout.write(self.style.SUCCESS("  ✓ Content classification complete"))

        # 4. Calculate comprehensive scores (personalization, trend, serendipity)
        recent_articles = Article.objects.all()[:200]  # For trend analysis
        articles_to_score = Article.objects.filter(
            relevance_score__gt=0,
            personalization_score=0  # Haven't been personalized yet
        )[:100]

        if articles_to_score.exists():
            self.stdout.write(f"\n[4/4] Calculating personalized scores for {articles_to_score.count()} articles...")

            for article in articles_to_score:
                final_score = score_article_comprehensive(
                    article,
                    user_prefs,
                    reading_context,
                    recent_articles
                )
                article.save()

                # Show sample for first 5
                if article.id <= 5:
                    self.stdout.write(
                        f"  • {article.title[:40]}... "
                        f"[P:{article.personalization_score:.0f} "
                        f"T:{article.trend_score:.0f} "
                        f"S:{article.serendipity_score:.0f} "
                        f"→ Final:{final_score:.0f}]"
                    )

            self.stdout.write(self.style.SUCCESS("  ✓ Personalization complete"))

        # Summary
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("Curation Complete!"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        if user_prefs:
            self.stdout.write(f"User: {user.username}")
            self.stdout.write(f"Total feedback: {user_prefs.total_feedback_count}")
            self.stdout.write(f"Top interests: {', '.join(user_prefs.interest_keywords[:5])}")
            self.stdout.write("\nRun with --update-preferences to refresh user learning.")
