"""Search an embedded SmartTouch documentation index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .openai_embeddings import OpenAIEmbeddingProvider
from .semantic_search import rank_records, rank_records_hybrid


def load_records(path: Path) -> list[dict]:
    records = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON at line {line_number}") from error
    return records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search embedded SmartTouch documentation."
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("build/embedded-chunks.jsonl"),
    )
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--model", default="text-embedding-3-small")
    parser.add_argument(
        "--mode",
        choices=("semantic", "hybrid"),
        default="hybrid",
        help="Use semantic-only search or semantic plus lexical fusion.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.index.is_file():
        print(f"Index does not exist: {args.index}")
        return 2

    records = load_records(args.index)
    if not records:
        print("Index contains no records")
        return 2

    provider = OpenAIEmbeddingProvider(model=args.model)
    query_vector = provider.embed([args.query])[0].vector
    print(f"Query: {args.query}")
    print(f"Mode: {args.mode}\n")

    if args.mode == "semantic":
        ranked = rank_records(query_vector, records, limit=args.limit)
        for position, (score, record) in enumerate(ranked, start=1):
            print(f"{position}. Semantic score: {score:.4f}")
            _print_record(record)
    else:
        ranked = rank_records_hybrid(
            args.query,
            query_vector,
            records,
            limit=args.limit,
        )
        for position, result in enumerate(ranked, start=1):
            lexical_rank = result.lexical_rank or "-"
            promotion = " | phrase promoted" if result.lexical_promoted else ""
            print(
                f"{position}. Final: {result.final_score:.6f} | "
                f"semantic: {result.semantic_score:.4f} "
                f"(rank {result.semantic_rank}) | "
                f"lexical: {result.lexical_score:.4f} "
                f"(rank {lexical_rank}){promotion}"
            )
            _print_record(result.record)

    return 0


def _print_record(record: dict) -> None:
    heading = " > ".join(record["heading_path"])
    print(f"   Heading: {heading}")
    print(f"   Source: {record['source_path']}")
    if record.get("source_url"):
        print(f"   URL: {record['source_url']}")
    print()


if __name__ == "__main__":
    raise SystemExit(main())
