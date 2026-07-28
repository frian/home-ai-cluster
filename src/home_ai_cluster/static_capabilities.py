"""Bounded capability contract shared by static-cluster construction."""

from collections.abc import Sequence

DEFAULT_STATIC_CAPABILITY_NAMES = ("chat", "summarize")
_VALID_STATIC_CAPABILITY_NAMES = frozenset(DEFAULT_STATIC_CAPABILITY_NAMES)


def validate_static_capabilities(
    value: Sequence[object],
    *,
    subject: str,
) -> tuple[str, ...]:
    """Validate one explicit bounded static capability set."""
    if not value:
        raise ValueError(f"{subject} capabilities must not be empty")
    if any(not isinstance(name, str) for name in value):
        raise ValueError(f"{subject} capability must be a string")
    if any(name not in _VALID_STATIC_CAPABILITY_NAMES for name in value):
        raise ValueError(f"unknown {subject} capability")
    if len(value) != len(set(value)):
        raise ValueError(f"duplicate {subject} capability")
    return tuple(value)
