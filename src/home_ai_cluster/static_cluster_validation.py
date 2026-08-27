"""Shared validation for the accepted static cluster topology facts."""

import argparse
from urllib.parse import urlsplit

LOCAL_NODE_ID = "local"


def remote_node_id(value: str) -> str:
    """Validate one explicit cluster-owned remote node identifier."""
    if not value.strip():
        raise argparse.ArgumentTypeError("remote node id must not be empty")
    if value == LOCAL_NODE_ID:
        raise argparse.ArgumentTypeError("remote node id must differ from local")
    return value


def remote_base_url(value: str) -> str:
    """Validate and normalize one explicit remote HTTP base URL."""
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        _port = parsed.port
    except ValueError:
        raise argparse.ArgumentTypeError(
            "remote base URL must be an absolute http:// or https:// URL"
        ) from None

    if (
        parsed.scheme not in {"http", "https"}
        or host is None
        or parsed.username is not None
        or parsed.netloc.endswith(":")
        or parsed.path not in {"", "/"}
        or "?" in value
        or "#" in value
    ):
        raise argparse.ArgumentTypeError(
            "remote base URL must be an absolute http:// or https:// URL"
        )
    return value[:-1] if parsed.path == "/" else value
