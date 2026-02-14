"""
Service for extracting metadata from YouTube videos and podcasts.
Uses yt-dlp for YouTube (free, no API key needed) and RSS parsing for podcasts.
"""
import subprocess
import json
import re
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


def is_youtube_url(url):
    """Check if URL is a YouTube video."""
    youtube_domains = ['youtube.com', 'youtu.be', 'm.youtube.com']
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    return any(domain == d or domain.endswith('.' + d) for d in youtube_domains)


def extract_youtube_metadata(url):
    """
    Extract metadata from YouTube video using yt-dlp.
    Returns dict with: duration_seconds, author, view_count, description, thumbnail

    Note: Requires yt-dlp to be installed: pip install yt-dlp
    """
    if not is_youtube_url(url):
        return None

    # Validate URL scheme for security (prevent command injection)
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        logger.warning(f"Invalid URL scheme for YouTube metadata: {parsed.scheme}")
        return None

    try:
        # Use yt-dlp to extract metadata (no download, just info)
        result = subprocess.run(
            ['yt-dlp', '--dump-json', '--no-download', '--no-warnings', url],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)

            return {
                'duration_seconds': data.get('duration'),
                'author': data.get('uploader') or data.get('channel'),
                'view_count': data.get('view_count'),
                'description': data.get('description', '')[:1000],  # Limit description
                'thumbnail': data.get('thumbnail'),
                'title': data.get('title'),  # In case FreshRSS title is truncated
            }
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error extracting YouTube metadata: {e}")

    return None


def is_podcast_url(url):
    """Check if URL is likely a podcast (audio file or podcast URL)."""
    audio_extensions = ['.mp3', '.m4a', '.ogg', '.wav', '.aac']
    podcast_domains = ['podcasts.apple.com', 'spotify.com', 'soundcloud.com', 'pocketcasts.com']

    parsed = urlparse(url)
    path_lower = parsed.path.lower()

    # Check for audio file extensions
    if any(path_lower.endswith(ext) for ext in audio_extensions):
        return True

    # Check for podcast hosting domains
    if any(domain in parsed.netloc for domain in podcast_domains):
        return True

    return False


def extract_podcast_metadata(url, description=''):
    """
    Extract podcast metadata.
    For now, uses simple heuristics and RSS data.
    Returns dict with: duration_seconds, author, description
    """
    if not is_podcast_url(url):
        return None

    # Try to extract duration from description using common patterns
    # Example: "Duration: 45:30" or "Length: 1h 20m"
    duration_seconds = None

    # Pattern: HH:MM:SS or MM:SS
    time_pattern = re.search(r'(\d{1,2}):(\d{2})(?::(\d{2}))?', description)
    if time_pattern:
        hours = 0
        if time_pattern.group(3):  # HH:MM:SS
            hours = int(time_pattern.group(1))
            minutes = int(time_pattern.group(2))
            seconds = int(time_pattern.group(3))
        else:  # MM:SS
            minutes = int(time_pattern.group(1))
            seconds = int(time_pattern.group(2))

        duration_seconds = hours * 3600 + minutes * 60 + seconds

    # Pattern: "1h 20m" or "45m"
    duration_pattern = re.search(r'(?:(\d+)h\s*)?(?:(\d+)m)?', description.lower())
    if duration_pattern and not duration_seconds:
        hours = int(duration_pattern.group(1) or 0)
        minutes = int(duration_pattern.group(2) or 0)
        duration_seconds = hours * 3600 + minutes * 60

    return {
        'duration_seconds': duration_seconds,
        'author': None,  # Would need RSS parsing to get this
        'description': description,
    }


def enrich_article_with_metadata(article):
    """
    Enrich an article with metadata based on its source type.
    Modifies the article in-place and saves it.
    """
    if not article.source:
        return False

    # YouTube metadata
    if article.source.source_type == 'yt' or is_youtube_url(article.link):
        metadata = extract_youtube_metadata(article.link)
        if metadata:
            article.duration_seconds = metadata.get('duration_seconds')
            article.author = metadata.get('author', '')[:200]  # Limit to field max
            article.view_count = metadata.get('view_count')
            if metadata.get('description') and not article.description:
                article.description = metadata['description']
            if metadata.get('thumbnail') and not article.image_url:
                article.image_url = metadata['thumbnail']
            if metadata.get('title'):
                article.title = metadata['title']

            article.save()
            return True

    # Podcast metadata
    elif article.source.source_type == 'podcast' or is_podcast_url(article.link):
        metadata = extract_podcast_metadata(article.link, article.description)
        if metadata and metadata.get('duration_seconds'):
            article.duration_seconds = metadata['duration_seconds']
            if metadata.get('author'):
                article.author = metadata['author'][:200]
            article.save()
            return True

    return False


def format_duration(seconds):
    """
    Format duration in seconds to human-readable string.
    Examples: "5:30", "1:20:45"
    """
    if not seconds:
        return None

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"
