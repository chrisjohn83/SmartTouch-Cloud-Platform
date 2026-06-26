"""Search SmartTouch documentation using PostgreSQL and pgvector."""

from __future__ import annotations

import argparse

from .openai_embeddings import OpenAIEmbeddingProvider
from .postgres_search import (
    database_url_from_environment,
    search_postgres,
    search_postgres_hybrid,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search SmartTouch documentation stored in pgvector."
    )
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--model",
        default="text-embedding-3-small",
    )
    parser.add_argument(
        "--mode",
        choices=("semantic", "hybrid"),
        default="hybrid",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.limit < 1:
        print("--limit must be at least 1")
        return 2

    try:
        database_url = database_url_from_environment()

        provider = OpenAIEmbeddingProvider(model=args.model)
        query_vector = provider.embed([args.query])[0].vector

        if args.mode == "semantic":
            results = search_postgres(
                query_vector,
                database_url=database_url,
                limit=args.limit,
            )
        else:
            results = search_postgres_hybrid(
                args.query,
                query_vector,
                database_url=database_url,
                limit=args.limit,
            )
    except (RuntimeError, ValueError) as error:
        print(f"Error: {error}")
        return 2

    print(f"Query: {args.query}")
    print("Backend: PostgreSQL/pgvector\n")

    if not results:
        print("No matching documentation found")
        return 0

    for position, record in enumerate(results, start=1):
        heading_path = record.get("heading_path") or []
        heading = " > ".join(heading_path)

        if args.mode == "semantic":
            print(f"{position}. Score: {float(record['score']):.4f}")
        else:
            semantic_rank = record.get("semantic_rank") or "-"
            lexical_rank = record.get("lexical_rank") or "-"

            print(
                f"{position}. Final: {record['final_score']:.6f} | "
                f"semantic: {record['semantic_score']:.4f} "
                f"(rank {semantic_rank}) | "
                f"lexical: {record['lexical_score']:.4f} "
                f"(rank {lexical_rank})"
            )

        print(f"   Heading: {heading}")
        print(f"   Source: {record['source_path']}")

        if record.get("source_url"):
            print(f"   URL: {record['source_url']}")

        print()

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
