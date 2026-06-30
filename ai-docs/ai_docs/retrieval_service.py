"""Service layer for SmartTouch documentation retrieval."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol
from .answer_context import build_answer_context
from .answer_generator import AnswerModelClient, generate_answer
from .openai_answer_client import OpenAIAnswerClient
from .config import load_config
from .knowledge_graph_query import expand_query_with_graph

from .openai_embeddings import OpenAIEmbeddingProvider
from .postgres_search import (
    database_url_from_environment,
    search_postgres_hybrid,
)
from .retrieval_api import build_search_response

class RetrievalServiceError(RuntimeError):
    """Raised when retrieval dependencies are unavailable."""

class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[Any]:
        ...


SearchFunction = Callable[..., list[dict[str, Any]]]


def _search_postgres_from_config(
    query: str,
    query_vector: list[float],
    *,
    limit: int = 5,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    resolved_url = database_url_from_environment() if database_url is None else database_url
    return search_postgres_hybrid(
        query,
        query_vector,
        limit=limit,
        database_url=resolved_url,
    )


def search_documentation(
    query: str,
    *,
    limit: int = 5,
    model: str | None = None,
    embedding_provider: Any | None = None,
    search_function: Any | None = None,
    database_url: str | None = None,
    knowledge_graph: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Search SmartTouch documentation."""

    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query is required")

    if limit < 1:
        raise ValueError("limit must be at least 1")

    config = load_config()
    embedding_model = model or config.embedding_model

    provider = embedding_provider or OpenAIEmbeddingProvider(model=embedding_model)
    search_fn = search_function or _search_postgres_from_config

    retrieval_query = normalized_query
    if knowledge_graph is not None:
        expansion = expand_query_with_graph(normalized_query, knowledge_graph)
        retrieval_query = expansion["expanded_query"]

    try:
        query_vector = provider.embed([retrieval_query])[0].vector
        results = search_fn(
            retrieval_query,
            query_vector,
            limit=limit,
        )
    except Exception as error:
        raise RetrievalServiceError(
            "Retrieval service is unavailable"
        ) from error

    return build_search_response(normalized_query, results)


def get_answer_context(
    query: str,
    *,
    limit: int = 5,
    model: str = "text-embedding-3-small",
    database_url: str | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    search_function: SearchFunction | None = None,
    max_content_chars: int | None = None,
    knowledge_graph: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = load_config()

    if max_content_chars is None:
        max_content_chars = config.max_context_chars

    search_response = search_documentation(
        query,
        limit=limit,
        model=model,
        database_url=database_url,
        embedding_provider=embedding_provider,
        search_function=search_function,
        knowledge_graph=knowledge_graph,
    )

    return build_answer_context(
        search_response,
        max_results=limit,
        max_content_chars=max_content_chars,
    )

def answer_question(
    query: str,
    *,
    model_client: AnswerModelClient | None = None,
    answer_model: str | None = None,
    model: str = "text-embedding-3-small",
    limit: int = 5,
    database_url: str | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    search_function: SearchFunction | None = None,
    max_content_chars: int = 1200,
    knowledge_graph: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Answer a question using SmartTouch documentation."""
    config = load_config()
    answer_model_name = answer_model or config.answer_model

    if model_client is None:
        model_client = OpenAIAnswerClient(model=answer_model_name)

    answer_context = get_answer_context(
        query,
        limit=limit,
        model=model,
        database_url=database_url,
        embedding_provider=embedding_provider,
        search_function=search_function,
        max_content_chars=max_content_chars,
        knowledge_graph=knowledge_graph,
    )
    try:
        return generate_answer(
            answer_context,
            model_client=model_client,
        )
    except Exception as error:
        raise RetrievalServiceError(
            "Answer generation service is unavailable"
        ) from error