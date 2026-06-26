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
LEXICAL_SEARCH_SQL = """
WITH query AS (
    SELECT websearch_to_tsquery('english', %s) AS value
)
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
    ts_rank_cd(search_vector, query.value) AS score
FROM document_chunks, query
WHERE search_vector @@ query.value
ORDER BY score DESC, id
LIMIT %s
"""

LEXICAL_SEARCH_SQL = """
WITH query AS (
    SELECT websearch_to_tsquery('english', %s) AS value
)
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
    ts_rank_cd(search_vector, query.value) AS score
FROM document_chunks, query
WHERE search_vector @@ query.value
ORDER BY score DESC, id
LIMIT %s
"""
def test_lexical_search_rejects_empty_query(self) -> None:
    from ai_docs.postgres_search import (
    search_postgres,
    search_postgres_lexical,
)

    with self.assertRaisesRegex(ValueError, "must not be empty"):
        search_postgres_lexical(
            "   ",
            database_url="postgresql://unused",
        )

    def test_lexical_search_rejects_empty_query(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            search_postgres_lexical(
                "   ",
                database_url="postgresql://unused",
            )

    def test_lexical_search_rejects_invalid_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 1"):
            search_postgres_lexical(
                "session already open",
                database_url="postgresql://unused",
                limit=0,
            )

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

def search_postgres_lexical(
    query: str,
    *,
    database_url: str,
    limit: int = 5,
) -> list[dict]:
    """Search document chunks using PostgreSQL full-text search."""

    normalized_query = query.strip()

    if not normalized_query:
        raise ValueError("query must not be empty")

    if limit < 1:
        raise ValueError("limit must be at least 1")

    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                LEXICAL_SEARCH_SQL,
                (normalized_query, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

def database_url_from_environment() -> str:
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is required")

    return database_url

def test_lexical_search_rejects_empty_query(self) -> None:
    from ai_docs.postgres_search import search_postgres_lexical

    with self.assertRaisesRegex(ValueError, "must not be empty"):
        search_postgres_lexical(
            "   ",
            database_url="postgresql://unused",
        )


def test_lexical_search_rejects_invalid_limit(self) -> None:
    from ai_docs.postgres_search import search_postgres_lexical

    with self.assertRaisesRegex(ValueError, "at least 1"):
        search_postgres_lexical(
            "session already open",
            database_url="postgresql://unused",
            limit=0,
        )

def test_lexical_search_rejects_invalid_limit(self) -> None:
    from ai_docs.postgres_search import search_postgres_lexical

    with self.assertRaisesRegex(ValueError, "at least 1"):
        search_postgres_lexical(
            "session already open",
            database_url="postgresql://unused",
            limit=0,
        )

def fuse_postgres_results(
    semantic_results: list[dict],
    lexical_results: list[dict],
    *,
    limit: int = 5,
    rrf_k: int = 60,
    semantic_weight: float = 0.45,
    lexical_weight: float = 0.55,
) -> list[dict]:
    """Combine semantic and lexical rankings without mutating records."""

    if limit < 1:
        raise ValueError("limit must be at least 1")

    combined: dict[str, dict] = {}

    for rank, record in enumerate(semantic_results, start=1):
        chunk_id = record["id"]
        combined[chunk_id] = {
            **record,
            "semantic_score": float(record["score"]),
            "semantic_rank": rank,
            "lexical_score": 0.0,
            "lexical_rank": None,
            "final_score": semantic_weight / (rrf_k + rank),
        }

    for rank, record in enumerate(lexical_results, start=1):
        chunk_id = record["id"]

        if chunk_id not in combined:
            combined[chunk_id] = {
                **record,
                "semantic_score": 0.0,
                "semantic_rank": None,
                "lexical_score": float(record["score"]),
                "lexical_rank": rank,
                "final_score": 0.0,
            }
        else:
            combined[chunk_id]["lexical_score"] = float(record["score"])
            combined[chunk_id]["lexical_rank"] = rank

        combined[chunk_id]["final_score"] += (
            lexical_weight / (rrf_k + rank)
        )

    ranked = sorted(
        combined.values(),
        key=lambda record: (-record["final_score"], record["id"]),
    )

    return ranked[:limit]

def test_fuses_semantic_and_lexical_results(self) -> None:
    from ai_docs.postgres_search import fuse_postgres_results

    semantic = [
        {"id": "general", "score": 0.8},
        {"id": "exact-error", "score": 0.6},
    ]
    lexical = [
        {"id": "exact-error", "score": 1.1},
        {"id": "general", "score": 0.1},
    ]

    original_semantic = [record.copy() for record in semantic]
    original_lexical = [record.copy() for record in lexical]

    results = fuse_postgres_results(
        semantic,
        lexical,
        limit=2,
    )

    self.assertEqual(results[0]["id"], "exact-error")
    self.assertEqual(results[0]["lexical_rank"], 1)
    self.assertEqual(results[0]["semantic_rank"], 2)
    self.assertEqual(semantic, original_semantic)
    self.assertEqual(lexical, original_lexical)

def search_postgres_hybrid(
    query: str,
    query_vector: Sequence[float],
    *,
    database_url: str,
    limit: int = 5,
    candidate_limit: int = 50,
) -> list[dict]:
    """Search semantic and lexical candidates, then fuse their ranks."""

    if limit < 1:
        raise ValueError("limit must be at least 1")

    if candidate_limit < limit:
        raise ValueError("candidate_limit must be at least limit")

    semantic_results = search_postgres(
        query_vector,
        database_url=database_url,
        limit=candidate_limit,
    )
    lexical_results = search_postgres_lexical(
        query,
        database_url=database_url,
        limit=candidate_limit,
    )

    return fuse_postgres_results(
        semantic_results,
        lexical_results,
        limit=limit,
    )
