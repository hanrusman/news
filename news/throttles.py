"""
Custom throttle classes for API rate limiting.
"""
from rest_framework.throttling import UserRateThrottle


class IngestThrottle(UserRateThrottle):
    """
    Throttle for article ingestion endpoints.
    Limit: 500 requests per hour per user.
    """
    scope = 'ingest'


class CurationThrottle(UserRateThrottle):
    """
    Throttle for expensive AI curation operations.
    Limit: 10 requests per hour per user.
    """
    scope = 'curation'
