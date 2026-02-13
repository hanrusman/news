from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from news.models import ReadingContext, Category

class Command(BaseCommand):
    help = 'Sets up default reading contexts for users'

    def handle(self, *args, **options):
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("No users found. Create a superuser first."))
            return

        # Check if contexts already exist
        if ReadingContext.objects.filter(user=user).exists():
            self.stdout.write(self.style.WARNING(f"Contexts already exist for {user.username}"))
            return

        # Create default contexts
        contexts = [
            {
                'name': 'Morning Briefing',
                'content_depth': 'light',
                'relevance_weight': 0.5,
                'personalization_weight': 0.3,
                'serendipity_weight': 0.05,
                'trend_weight': 0.3,
            },
            {
                'name': 'Deep Dive',
                'content_depth': 'heavy',
                'relevance_weight': 0.4,
                'personalization_weight': 0.4,
                'serendipity_weight': 0.1,
                'trend_weight': 0.1,
            },
            {
                'name': 'Balanced',
                'content_depth': 'medium',
                'relevance_weight': 0.4,
                'personalization_weight': 0.3,
                'serendipity_weight': 0.1,
                'trend_weight': 0.2,
                'is_active': True,  # Default active
            },
            {
                'name': 'Discovery Mode',
                'content_depth': 'medium',
                'relevance_weight': 0.2,
                'personalization_weight': 0.2,
                'serendipity_weight': 0.4,  # High serendipity
                'trend_weight': 0.2,
            },
            {
                'name': 'Trending Topics',
                'content_depth': 'light',
                'relevance_weight': 0.3,
                'personalization_weight': 0.2,
                'serendipity_weight': 0.05,
                'trend_weight': 0.5,  # High trend focus
            },
        ]

        for ctx_data in contexts:
            ctx = ReadingContext.objects.create(user=user, **ctx_data)
            self.stdout.write(self.style.SUCCESS(f"✓ Created context: {ctx.name}"))

        self.stdout.write(self.style.SUCCESS(f"\nCreated {len(contexts)} reading contexts for {user.username}"))
        self.stdout.write("Use the UI to switch between contexts based on your mood!")
