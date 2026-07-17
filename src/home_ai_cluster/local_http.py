"""Validation for explicitly supplied local HTTP runtime addresses."""

import argparse
from urllib.parse import urlsplit

LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}


def local_http_url(value: str) -> str:
    """Validate one absolute loopback HTTP URL without contacting it."""
    parsed = urlsplit(value)
    if parsed.scheme != "http" or parsed.hostname not in LOCAL_HOSTS:
        raise argparse.ArgumentTypeError(
            "runtime URL must be an absolute loopback http:// URL"
        )
    return value.rstrip("/")
