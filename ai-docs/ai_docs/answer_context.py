"""Build grounded answer context from retrieval results."""

from __future__ import annotations

from typing import Any


def build_answer_context(
    search_response: dict[str, Any],
    *,
    max_results: int = 5,
    max_content_chars: int = 1200,
) -> dict[str, Any]:
    """Build citation-ready context from a retrieval response."""

    if max_results < 1:
        raise ValueError("max_results must be at least 1")

    if max_content_chars < 1:
        raise ValueError("max_content_chars must be at least 1")

    query = str(search_response.get("query", "")).strip()
    results = search_response.get("results") or []

    context_items = [
        _build_context_item(index, result, max_content_chars=max_content_chars)
        for index, result in enumerate(results[:max_results], start=1)
    ]

    return {
        "query": query,
        "context_count": len(context_items),
        "contexts": context_items,
    }


def _build_context_item(
    index: int,
    result: dict[str, Any],
    *,
    max_content_chars: int,
) -> dict[str, Any]:
    content = str(result.get("content") or "").strip()
    excerpt = _truncate(content, max_content_chars)

    heading_path = list(result.get("heading_path") or [])
    heading = " > ".join(str(part) for part in heading_path)

    return {
        "citation_id": f"source-{index}",
        "title": result.get("title"),
        "heading": result.get("heading"),
        "heading_path": heading_path,
        "heading_label": heading,
        "source_path": result.get("source_path"),
        "source_url": result.get("source_url"),
        "excerpt": excerpt,
        "scores": result.get("scores") or {},
        "ranks": result.get("ranks") or {},
    }


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text

    return text[: max_chars - 1].rstrip() + "…"
