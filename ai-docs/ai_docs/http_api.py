"""HTTP-facing request handlers for SmartTouch documentation retrieval."""

from __future__ import annotations

import os
from typing import Any

from .config import load_config
from .retrieval_service import (
    answer_question,
    get_answer_context,
    search_documentation,
)


def health_response() -> dict[str, Any]:
    """Return service health."""

    return {
        "status": "ok",
        "service": "smarttouch-ai-docs",
    }

def diagnostics_response() -> dict[str, Any]:
    """Return non-secret service diagnostics."""

    config = load_config()

    return {
        "status": "ok",
        "service": "smarttouch-ai-docs",
        "database_configured": bool(config.database_url),
        "openai_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "embedding_model": config.embedding_model,
        "answer_model": config.answer_model,
        "default_retrieval_limit": config.default_retrieval_limit,
        "max_context_chars": config.max_context_chars,
    }

def handle_search_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle a search request payload."""

    config = load_config()
    query = _required_query(payload)
    limit = _limit(payload)
    model = str(payload.get("model", config.embedding_model))
    use_knowledge_graph = _use_knowledge_graph(payload)

    return search_documentation(
        query,
        limit=limit,
        model=model,
        use_knowledge_graph=use_knowledge_graph,
    )


def handle_answer_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle a grounded answer request payload."""

    config = load_config()
    query = _required_query(payload)
    limit = _limit(payload)
    model = str(payload.get("model", config.embedding_model))
    answer_model = str(payload.get("answer_model", config.answer_model))
    max_content_chars = _max_content_chars(payload)
    use_knowledge_graph = _use_knowledge_graph(payload)

    return answer_question(
        query,
        limit=limit,
        model=model,
        answer_model=answer_model,
        max_content_chars=max_content_chars,
        use_knowledge_graph=use_knowledge_graph,
    )


def handle_answer_context_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle an answer-context request payload."""

    config = load_config()
    query = _required_query(payload)
    limit = _limit(payload)
    model = str(payload.get("model", config.embedding_model))
    max_content_chars = _max_content_chars(payload)
    use_knowledge_graph = _use_knowledge_graph(payload)

    return get_answer_context(
        query,
        limit=limit,
        model=model,
        max_content_chars=max_content_chars,
        use_knowledge_graph=use_knowledge_graph,
    )


def _required_query(payload: dict[str, Any]) -> str:
    query = str(payload.get("query", "")).strip()

    if not query:
        raise ValueError("query is required")

    return query


def _limit(payload: dict[str, Any]) -> int:
    config = load_config()
    raw_limit = payload.get("limit", config.default_retrieval_limit)

    try:
        limit = int(raw_limit)
    except (TypeError, ValueError) as error:
        raise ValueError("limit must be an integer") from error

    if limit < 1:
        raise ValueError("limit must be at least 1")

    return limit


def _max_content_chars(payload: dict[str, Any]) -> int:
    config = load_config()
    raw_max_content_chars = payload.get(
        "max_content_chars",
        config.max_context_chars,
    )

    try:
        max_content_chars = int(raw_max_content_chars)
    except (TypeError, ValueError) as error:
        raise ValueError("max_content_chars must be an integer") from error

    if max_content_chars < 1:
        raise ValueError("max_content_chars must be at least 1")

    return max_content_chars


def _use_knowledge_graph(payload: dict[str, Any]) -> bool:
    return bool(payload.get("use_knowledge_graph", False))
