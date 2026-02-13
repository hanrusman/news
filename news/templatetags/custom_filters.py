from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


@register.filter(name='format_duration')
def format_duration(seconds):
    """
    Format duration in seconds to human-readable string.
    Examples: "5:30", "1:20:45"
    """
    if not seconds:
        return ""

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


@register.filter(name='score_color')
def score_color(score):
    """
    Return CSS color class based on score value (0-100).
    """
    if score >= 80:
        return 'text-green-400'
    elif score >= 60:
        return 'text-blue-400'
    elif score >= 40:
        return 'text-yellow-400'
    else:
        return 'text-gray-400'


@register.filter(name='score_bar_width')
def score_bar_width(score):
    """
    Return width percentage for score visualization.
    """
    return f"{max(0, min(100, score))}%"
