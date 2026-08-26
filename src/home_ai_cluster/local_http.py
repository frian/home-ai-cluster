"""Validation for explicitly supplied local HTTP runtime addresses."""

import argparse
from urllib.parse import urlsplit

LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}


def local_http_url(value: str) -> str:
    """Validate one absolute loopback HTTP URL without contacting it."""
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        _port = parsed.port
    except ValueError:
        raise argparse.ArgumentTypeError(
            "runtime URL must be an absolute loopback http:// URL"
        ) from None

    if (
        parsed.scheme != "http"
        or host not in LOCAL_HOSTS
        or parsed.username is not None
        or parsed.path not in {"", "/"}
        or "?" in value
        or "#" in value
    ):
        raise argparse.ArgumentTypeError(
            "runtime URL must be an absolute loopback http:// URL"
        )
    return value[:-1] if parsed.path == "/" else value
