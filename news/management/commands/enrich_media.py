from django.core.management.base import BaseCommand
from news.models import Article
from news.media_service import enrich_article_with_metadata, format_duration


class Command(BaseCommand):
    help = 'Enrich YouTube videos and podcasts with metadata (duration, author, views)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Number of articles to process (default: 20)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Process all articles (ignores --limit)',
        )

    def handle(self, *args, **options):
        # Find articles that need metadata enrichment
        # (YouTube/Podcast articles without duration)
        articles_query = Article.objects.filter(
            source__source_type__in=['yt', 'podcast'],
            duration_seconds__isnull=True
        )

        if not options['all']:
            articles_query = articles_query[:options['limit']]

        articles = list(articles_query)

        if not articles:
            self.stdout.write(self.style.WARNING("No articles need metadata enrichment."))
            return

        self.stdout.write(f"\nEnriching {len(articles)} articles with metadata...")
        self.stdout.write("=" * 60)

        success_count = 0
        for article in articles:
            self.stdout.write(f"\n• {article.title[:50]}...")

            try:
                if enrich_article_with_metadata(article):
                    success_count += 1

                    # Display enriched data
                    if article.duration_seconds:
                        duration_str = format_duration(article.duration_seconds)
                        self.stdout.write(f"  Duration: {duration_str}")
                    if article.author:
                        self.stdout.write(f"  Author: {article.author}")
                    if article.view_count:
                        self.stdout.write(f"  Views: {article.view_count:,}")

                    self.stdout.write(self.style.SUCCESS("  ✓ Enriched"))
                else:
                    self.stdout.write(self.style.WARNING("  ⚠ Could not extract metadata"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Error: {e}"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(
            f"\nCompleted! Successfully enriched {success_count}/{len(articles)} articles."
        ))

        if success_count < len(articles):
            self.stdout.write(self.style.WARNING(
                "\nNote: Some articles could not be enriched. This is normal for:"
                "\n  - Videos that have been deleted"
                "\n  - Podcasts without duration info in RSS"
                "\n  - Rate-limited requests (try again later)"
            ))
