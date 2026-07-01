"""Load persisted SmartTouch documentation knowledge graph files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ENTITIES_FILE = "kg-entities.jsonl"
RELATIONSHIPS_FILE = "kg-relationships.jsonl"


def load_knowledge_graph(graph_dir: Path) -> dict[str, list[dict[str, Any]]] | None:
    """Load knowledge graph entities and relationships from JSONL files."""

    entities_path = graph_dir / ENTITIES_FILE
    relationships_path = graph_dir / RELATIONSHIPS_FILE

    if not entities_path.is_file() or not relationships_path.is_file():
        return None

    return {
        "entities": _load_jsonl(entities_path),
        "relationships": _load_jsonl(relationships_path),
    }


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []

    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON in {path} at line {line_number}"
                ) from error

    return records
