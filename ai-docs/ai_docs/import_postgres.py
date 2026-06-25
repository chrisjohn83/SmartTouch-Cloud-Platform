from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb


MODEL = "text-embedding-3-small"
DIMENSIONS = 1536


UPSERT_SQL = """
INSERT INTO document_chunks (
    id,
    source_path,
    source_url,
    title,
    heading,
    heading_path,
    content,
    content_hash,
    chunk_index,
    start_line,
    end_line,
    word_count,
    metadata,
    embedding_model,
    embedding_dimensions,
    embedding
)
VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s::vector
)
ON CONFLICT (id) DO UPDATE SET
    source_path = EXCLUDED.source_path,
    source_url = EXCLUDED.source_url,
    title = EXCLUDED.title,
    heading = EXCLUDED.heading,
    heading_path = EXCLUDED.heading_path,
    content = EXCLUDED.content,
    content_hash = EXCLUDED.content_hash,
    chunk_index = EXCLUDED.chunk_index,
    start_line = EXCLUDED.start_line,
    end_line = EXCLUDED.end_line,
    word_count = EXCLUDED.word_count,
    metadata = EXCLUDED.metadata,
    embedding_model = EXCLUDED.embedding_model,
    embedding_dimensions = EXCLUDED.embedding_dimensions,
    embedding = EXCLUDED.embedding,
    updated_at = now()
"""


def vector_literal(values: list[float]) -> str:
    if len(values) != DIMENSIONS:
        raise ValueError(
            f"Expected {DIMENSIONS} embedding values, got {len(values)}"
        )

    return "[" + ",".join(str(float(value)) for value in values) + "]"

def prepare_record(record: dict) -> tuple:
    embedding = record["embedding"]

    return (
        record["id"],
        record["source_path"],
        record.get("source_url"),
        record.get("title"),
        record.get("heading"),
        Jsonb(record.get("heading_path", [])),
        record["content"],
        record["content_hash"],
        record["chunk_index"],
        record.get("start_line"),
        record.get("end_line"),
        record.get("word_count"),
        Jsonb(record.get("metadata", {})),
        embedding["model"],
        embedding["dimensions"],
        vector_literal(embedding["vector"]),
    )

def import_jsonl(input_path: Path, database_url: str) -> int:
    rows = []

    with input_path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue

            try:
                rows.append(prepare_record(json.loads(line)))
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(
                    f"Invalid record at line {line_number}: {error}"
                ) from error

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(UPSERT_SQL, rows)

    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import embedded documentation chunks into PostgreSQL."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("build/full-embedded-chunks.jsonl"),
    )
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        parser.error("DATABASE_URL environment variable is required")

    count = import_jsonl(args.input, database_url)
    print(f"Imported {count} document chunks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
