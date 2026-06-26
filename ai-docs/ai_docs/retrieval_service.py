"""Service layer for SmartTouch documentation retrieval."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol
from .answer_context import build_answer_context

from .openai_embeddings import OpenAIEmbeddingProvider
from .postgres_search import (
    database_url_from_environment,
    search_postgres_hybrid,
)
from .retrieval_api import build_search_response


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[Any]:
        ...


SearchFunction = Callable[
    [str, list[float]],
    list[dict[str, Any]],
]


def search_documentation(
    query: str,
    *,
    limit: int = 5,
    model: str = "text-embedding-3-small",
    database_url: str | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    search_function: SearchFunction | None = None,
) -> dict[str, Any]:
    """Search SmartTouch documentation and return the API response contract."""

    normalized_query = query.strip()

    if not normalized_query:
        raise ValueError("query must not be empty")

    if limit < 1:
        raise ValueError("limit must be at least 1")

    provider = embedding_provider or OpenAIEmbeddingProvider(model=model)
    query_vector = provider.embed([normalized_query])[0].vector

    if search_function is None:
        resolved_database_url = database_url or database_url_from_environment()

        def search_function(
            search_query: str,
            search_vector: list[float],
        ) -> list[dict[str, Any]]:
            return search_postgres_hybrid(
                search_query,
                search_vector,
                database_url=resolved_database_url,
                limit=limit,
            )

    results = search_function(normalized_query, query_vector)

    return build_search_response(normalized_query, results)

def get_answer_context(
    query: str,
    *,
    limit: int = 5,
    model: str = "text-embedding-3-small",
    database_url: str | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    search_function: SearchFunction | None = None,
    max_content_chars: int = 1200,
) -> dict[str, Any]:
    """Retrieve SmartTouch docs and build citation-ready answer context."""

    search_response = search_documentation(
        query,
        limit=limit,
        model=model,
        database_url=database_url,
        embedding_provider=embedding_provider,
        search_function=search_function,
    )

    return build_answer_context(
        search_response,
        max_results=limit,
        max_content_chars=max_content_chars,
    )
