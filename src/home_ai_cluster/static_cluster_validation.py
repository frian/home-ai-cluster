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
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
        raise argparse.ArgumentTypeError(
            "remote base URL must be an absolute http:// or https:// URL"
        )
    return value.rstrip("/")
