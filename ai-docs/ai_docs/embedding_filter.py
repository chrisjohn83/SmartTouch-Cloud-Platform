"""Decide whether a documentation chunk should be embedded."""

from __future__ import annotations

import re
from typing import Any


IFRAME_RE = re.compile(
    r"<iframe\b[^>]*>.*?</iframe\s*>",
    flags=re.IGNORECASE | re.DOTALL,
)

MARKDOWN_HEADING_RE = re.compile(
    r"^\s{0,3}#{1,6}\s+.*$",
    flags=re.MULTILINE,
)


def searchable_text(content: str) -> str:
    """Remove markup that contributes no searchable information."""

    text = IFRAME_RE.sub("", content)
    text = MARKDOWN_HEADING_RE.sub("", text)
    return text.strip()


def should_embed(chunk: dict[str, Any]) -> bool:
    """Return True when a chunk contains searchable content."""

    content = str(chunk.get("content") or "")
    return bool(searchable_text(content))
