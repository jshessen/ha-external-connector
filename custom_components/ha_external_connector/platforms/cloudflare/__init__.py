"""CloudFlare platform implementation."""

from .client import CloudFlarePlatform
from .models import (
    AccessApplicationSpec,
    CloudFlareResourceType,
    DNSRecordSpec,
    ZoneSpec,
)

__all__ = [
    "CloudFlarePlatform",
    "CloudFlareResourceType",
    "AccessApplicationSpec",
    "DNSRecordSpec",
    "ZoneSpec",
]

# Note: helpers.py available for backward compatibility if needed
