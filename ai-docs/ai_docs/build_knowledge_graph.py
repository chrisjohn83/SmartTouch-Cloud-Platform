"""Build knowledge graph JSONL artifacts from SmartTouch documentation chunks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .knowledge_graph import extract_graph


def load_chunks(input_path: Path) -> list[dict[str, Any]]:
    """Load chunk records from JSONL."""

    chunks = []
    with input_path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                chunks.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON at line {line_number}: {input_path}"
                ) from error

    return chunks


def write_graph_jsonl(
    graph: dict[str, list[dict[str, Any]]],
    output_dir: Path,
) -> dict[str, int]:
    """Write graph entities and relationships to JSONL files."""

    output_dir.mkdir(parents=True, exist_ok=True)

    entities = graph.get("entities", [])
    relationships = graph.get("relationships", [])

    _write_jsonl(entities, output_dir / "kg-entities.jsonl")
    _write_jsonl(relationships, output_dir / "kg-relationships.jsonl")

    return {
        "entities": len(entities),
        "relationships": len(relationships),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build SmartTouch documentation knowledge graph JSONL."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("build/full-embedded-chunks.jsonl"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("build"),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    chunks = load_chunks(args.input)
    graph = extract_graph(chunks)
    counts = write_graph_jsonl(graph, args.output_dir)

    print(f"Entities: {counts['entities']}")
    print(f"Relationships: {counts['relationships']}")
    print(f"Output: {args.output_dir}")

    return 0


def _write_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            file.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
