from django.core.management.base import BaseCommand
from news.models import Category, Source
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Seeds the database with initial categories and feeds'

    def handle(self, *args, **options):
        data = {
            'Wereldnieuws': [
                ('NOS Nieuws', 'https://feeds.nos.nl/nosnieuwsalgemeen'),
                ('BBC World', 'http://feeds.bbci.co.uk/news/world/rss.xml'),
            ],
            'AI': [
                ('OpenAI Blog', 'https://openai.com/blog/rss.xml'),
                ('TLDR AI', 'https://tldr.tech/ai/feed'),
            ],
            'Haarlem en omgeving': [
                ('NH Nieuws Haarlem', 'https://www.nhnieuws.nl/rss/regio/haarlem'),
            ],
            'Opvoeden en Kids': [
                # Placeholder - user can add specific blogs
            ],
            'HR-tech en Future of Work': [
                ('TechCrunch', 'https://techcrunch.com/feed/'), 
            ],
            'Health': [
                ('Medical News Today', 'https://www.medicalnewstoday.com/feed'),
            ],
        }

        for cat_name, feeds in data.items():
            category, created = Category.objects.get_or_create(
                name=cat_name, 
                defaults={'slug': slugify(cat_name)}
            )
            if created:
                self.stdout.write(f'Created Category: {cat_name}')
            
            for feed_name, feed_url in feeds:
                Source.objects.get_or_create(
                    url=feed_url,
                    defaults={
                        'name': feed_name,
                        'category': category,
                        'source_type': 'rss'
                    }
                )
                self.stdout.write(f'  - Added Source: {feed_name}')

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
