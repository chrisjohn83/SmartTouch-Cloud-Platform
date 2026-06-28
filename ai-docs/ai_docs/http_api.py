"""HTTP-facing request handlers for SmartTouch documentation retrieval."""

from __future__ import annotations

from typing import Any

from .retrieval_service import get_answer_context, search_documentation
from .retrieval_service import answer_question


def health_response() -> dict[str, Any]:
    """Return service health."""

    return {
        "status": "ok",
        "service": "smarttouch-ai-docs",
    }


def handle_search_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle a search request payload."""

    query = _required_query(payload)
    limit = _limit(payload)

    return search_documentation(query, limit=limit)

def handle_answer_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle a grounded answer request payload."""

    query = _required_query(payload)
    limit = _limit(payload)
    answer_model = str(payload.get("answer_model", "gpt-5.4-mini"))

    return answer_question(
        query,
        limit=limit,
        answer_model=answer_model,
    )

def handle_answer_context_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle an answer-context request payload."""

    query = _required_query(payload)
    limit = _limit(payload)
    max_content_chars = int(payload.get("max_content_chars", 1200))

    return get_answer_context(
        query,
        limit=limit,
        max_content_chars=max_content_chars,
    )


def _required_query(payload: dict[str, Any]) -> str:
    query = str(payload.get("query", "")).strip()

    if not query:
        raise ValueError("query is required")

    return query


def _limit(payload: dict[str, Any]) -> int:
    limit = int(payload.get("limit", 5))

    if limit < 1:
        raise ValueError("limit must be at least 1")

    return limit
