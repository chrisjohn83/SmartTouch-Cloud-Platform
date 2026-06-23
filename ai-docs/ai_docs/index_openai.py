"""CLI for indexing SmartTouch chunks with OpenAI embeddings."""

from __future__ import annotations

import argparse
from pathlib import Path

from .embedding_index import index_embeddings
from .openai_embeddings import OpenAIEmbeddingProvider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate OpenAI embeddings for SmartTouch chunks."
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("build/chunks.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/embedded-chunks.jsonl"),
    )
    parser.add_argument(
        "--model",
        default="text-embedding-3-small",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of pending chunks to embed.",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if not args.input.is_file():
        print(f"Input file does not exist: {args.input}")
        return 2

    provider = OpenAIEmbeddingProvider(model=args.model)

    embedded, pending = index_embeddings(
        input_path=args.input,
        output_path=args.output,
        provider=provider,
        batch_size=args.batch_size,
        limit=args.limit,
    )

    print(f"Embedded {embedded} of {pending} selected pending chunks")
    print(f"Output: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
