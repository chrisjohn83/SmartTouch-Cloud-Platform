"""Response contract helpers for SmartTouch documentation retrieval."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def build_search_response(query: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a stable API-style response from ranked retrieval results."""

    return {
        "query": query,
        "result_count": len(results),
        "results": [_format_result(result) for result in results],
    }


def _format_result(record: dict[str, Any]) -> dict[str, Any]:
    heading_path = list(record.get("heading_path") or [])

    return {
        "id": record.get("id"),
        "title": record.get("title"),
        "heading": record.get("heading"),
        "heading_path": heading_path,
        "source_path": record.get("source_path"),
        "source_url": record.get("source_url"),
        "content": record.get("content"),
        "scores": {
            "final": record.get("final_score", record.get("score")),
            "semantic": record.get("semantic_score"),
            "lexical": record.get("lexical_score"),
        },
        "ranks": {
            "semantic": record.get("semantic_rank"),
            "lexical": record.get("lexical_rank"),
        },
        "metadata": deepcopy(record.get("metadata") or {}),
    }
