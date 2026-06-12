"""Shared utility helpers."""

from __future__ import annotations

import logging
import re
from typing import Iterable, List

logger = logging.getLogger(__name__)

# Basic but practical email validation pattern.
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def is_valid_email(email: str) -> bool:
    """Return True when the string looks like a valid email address."""
    if not email or not isinstance(email, str):
        return False
    return bool(_EMAIL_RE.match(email.strip()))


def truncate(text: str, max_chars: int = 4000) -> str:
    """Truncate text to a maximum number of characters with an ellipsis."""
    if text is None:
        return ""
    text = str(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + " ..."


def safe_filename(name: str) -> str:
    """Return just the filename portion of a path-like string."""
    if not name:
        return "unknown"
    return name.replace("\\", "/").split("/")[-1]


def dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    """Remove duplicates from an iterable while preserving order."""
    seen: set = set()
    result: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def format_page(page: object) -> str:
    """Format a 0-indexed page value into a human friendly 1-indexed string."""
    try:
        return str(int(page) + 1)
    except (TypeError, ValueError):
        return str(page) if page not in (None, "") else "N/A"
