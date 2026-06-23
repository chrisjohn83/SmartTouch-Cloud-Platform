"""Batch and persist documentation embeddings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Optional

from .embedding_filter import should_embed
from .embedding_input import build_embedding_input
from .embeddings import EmbeddingProvider


def batched(items: list[Any], size: int) -> Iterable[list[Any]]:
    if size < 1:
        raise ValueError("Batch size must be at least 1")

    for start in range(0, len(items), size):
        yield items[start : start + size]


def load_completed_ids(output: Path) -> set[str]:
    """Load successfully embedded chunk IDs for resume support."""

    if not output.exists():
        return set()

    completed: set[str] = set()

    with output.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                record = json.loads(line)
                completed.add(record["id"])
            except (json.JSONDecodeError, KeyError) as error:
                raise ValueError(
                    f"Invalid output record at line {line_number}"
                ) from error

    return completed


def load_pending_chunks(
    input_path: Path,
    completed_ids: set[str],
) -> list[dict[str, Any]]:
    """Load eligible chunks that have not already been embedded."""

    pending: list[dict[str, Any]] = []

    with input_path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                chunk = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid input JSON at line {line_number}"
                ) from error

            if chunk["id"] in completed_ids:
                continue

            if should_embed(chunk):
                pending.append(chunk)

    return pending


def index_embeddings(
    input_path: Path,
    output_path: Path,
    provider: EmbeddingProvider,
    batch_size: int = 32,
    limit: Optional[int] = None,
) -> tuple[int, int]:
    """Embed pending chunks and append successful batches to JSONL.

    limit: optionally limit the number of pending chunks to process
    (used for testing or partial indexing).
    """
    if limit is not None and limit < 1:
        raise ValueError("Limit must be at least 1")

    completed_ids = load_completed_ids(output_path)
    pending = load_pending_chunks(input_path, completed_ids)

    if limit is not None:
        pending = pending[:limit]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    embedded_count = 0

    with output_path.open("a", encoding="utf-8", newline="\n") as output:
        for batch_number, chunk_batch in enumerate(
            batched(pending, batch_size),
            start=1,
        ):
            texts = [
                build_embedding_input(chunk)
                for chunk in chunk_batch
            ]

            results = provider.embed(texts)

            if len(results) != len(chunk_batch):
                raise RuntimeError(
                    "Provider returned an unexpected result count"
                )

            for chunk, result in zip(chunk_batch, results):
                record = {
                    **chunk,
                    "embedding": {
                        "model": result.model,
                        "dimensions": result.dimensions,
                        "vector": result.vector,
                    },
                }

                output.write(
                    json.dumps(record, ensure_ascii=False) + "\n"
                )

            output.flush()
            embedded_count += len(chunk_batch)

            print(
                f"Completed batch {batch_number}: "
                f"{embedded_count}/{len(pending)}"
            )

    return embedded_count, len(pending)
