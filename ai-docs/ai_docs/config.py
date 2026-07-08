"""Configuration helpers for the SmartTouch AI docs service."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_ANSWER_MODEL = "gpt-5.4-mini"
DEFAULT_RETRIEVAL_LIMIT = 5
DEFAULT_MAX_CONTEXT_CHARS = 1200
DEFAULT_CORS_ORIGINS = (
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8001",
    "http://localhost:8000",
    "http://localhost:8001",
    "https://chrisjohn83.github.io",
)


@dataclass(frozen=True)
class AiDocsConfig:
    database_url: str | None
    embedding_model: str
    answer_model: str
    default_retrieval_limit: int
    max_context_chars: int
    cors_origins: tuple[str, ...]


def _read_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default

    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer") from error

    if value < 1:
        raise ValueError(f"{name} must be at least 1")

    return value


def _read_csv(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default

    values = tuple(
        value.strip()
        for value in raw.split(",")
        if value.strip()
    )
    return values or default


def load_config() -> AiDocsConfig:
    return AiDocsConfig(
        database_url=os.getenv("DATABASE_URL"),
        embedding_model=os.getenv(
            "AI_DOCS_EMBEDDING_MODEL",
            DEFAULT_EMBEDDING_MODEL,
        ),
        answer_model=os.getenv(
            "AI_DOCS_ANSWER_MODEL",
            DEFAULT_ANSWER_MODEL,
        ),
        default_retrieval_limit=_read_int(
            "AI_DOCS_DEFAULT_RETRIEVAL_LIMIT",
            DEFAULT_RETRIEVAL_LIMIT,
        ),
        max_context_chars=_read_int(
            "AI_DOCS_MAX_CONTEXT_CHARS",
            DEFAULT_MAX_CONTEXT_CHARS,
        ),
        cors_origins=_read_csv(
            "AI_DOCS_CORS_ORIGINS",
            DEFAULT_CORS_ORIGINS,
        ),
    )
