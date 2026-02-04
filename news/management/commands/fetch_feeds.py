import feedparser
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from time import mktime
from django.core.management.base import BaseCommand
from django.utils import timezone
from news.models import Source, Article

class Command(BaseCommand):
    help = 'Fetches new articles from all sources'

    def handle(self, *args, **options):
        sources = Source.objects.all()
        self.stdout.write(f'Fetching feeds for {sources.count()} sources...')

        total_new = 0

        for source in sources:
            self.stdout.write(f'Checking {source.name}...')
            try:
                feed = feedparser.parse(source.url)
                
                # Check for bozo error (malformed XML)
                if feed.bozo:
                    self.stdout.write(self.style.WARNING(f'  Feed Error: {feed.bozo_exception}'))
                    # Continue anyway as feedparser often salvages partial content

                for entry in feed.entries:
                    # Get GUID or fallback to link
                    guid = entry.get('id', entry.get('link'))
                    
                    if not guid:
                        continue

                    # Skip if exists
                    if Article.objects.filter(guid=guid).exists():
                        continue

                    # Parse Date
                    published = timezone.now()
                    if hasattr(entry, 'published_parsed'):
                        published = datetime.fromtimestamp(mktime(entry.published_parsed))
                        published = timezone.make_aware(published)
                    elif hasattr(entry, 'updated_parsed'):
                        published = datetime.fromtimestamp(mktime(entry.updated_parsed))
                        published = timezone.make_aware(published)

                    # Try to find an image
                    image_url = None
                    
                    # 1. Media Content / Thumbnails (YouTube/RSS extensions)
                    if 'media_content' in entry:
                         # Get first image
                         for media in entry.media_content:
                             if media.get('medium') == 'image' or media.get('type', '').startswith('image/'):
                                 image_url = media.get('url')
                                 break
                    
                    if not image_url and 'media_thumbnail' in entry:
                        # YouTube often puts it here
                        image_url = entry.media_thumbnail[0]['url']
                    
                    if not image_url and 'links' in entry:
                        # Look for enclosures
                        for link in entry.links:
                            if link.get('rel') == 'enclosure' and link.get('type', '').startswith('image/'):
                                image_url = link.get('href')
                                break
                    
                    # 2. Parse from Description/Content (HTML)
                    if not image_url:
                        html_content = ''
                        if 'content' in entry:
                            html_content = entry.content[0].value
                        elif 'summary' in entry:
                            html_content = entry.summary
                        
                        if html_content:
                            soup = BeautifulSoup(html_content, 'html.parser')
                            img = soup.find('img')
                            if img:
                                image_url = img.get('src')

                    # Create Article
                    Article.objects.create(
                        source=source,
                        title=entry.title,
                        link=entry.link,
                        description=entry.get('summary', '')[:5000], # Trucate just in case
                        pub_date=published,
                        guid=guid,
                        image_url=image_url
                    )
                    total_new += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Failed to parse {source.url}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully added {total_new} new articles.'))
