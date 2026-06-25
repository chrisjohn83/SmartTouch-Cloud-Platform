from __future__ import annotations

import os
from collections.abc import Sequence

import psycopg
from psycopg.rows import dict_row

from ai_docs.import_postgres import DIMENSIONS, vector_literal


SEARCH_SQL = """
SELECT
    id,
    source_path,
    source_url,
    title,
    heading,
    heading_path,
    content,
    metadata,
    embedding_model,
    1 - (embedding <=> %s::vector) AS score
FROM document_chunks
ORDER BY embedding <=> %s::vector
LIMIT %s
"""


def search_postgres(
    query_vector: Sequence[float],
    *,
    database_url: str,
    limit: int = 5,
) -> list[dict]:
    """Return document chunks nearest to the query embedding."""

    if len(query_vector) != DIMENSIONS:
        raise ValueError(
            f"Expected a {DIMENSIONS}-dimensional query vector, "
            f"got {len(query_vector)}"
        )

    if limit < 1:
        raise ValueError("limit must be at least 1")

    vector = vector_literal(list(query_vector))

    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(SEARCH_SQL, (vector, vector, limit))
            return [dict(row) for row in cursor.fetchall()]


def database_url_from_environment() -> str:
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is required")

    return database_url
