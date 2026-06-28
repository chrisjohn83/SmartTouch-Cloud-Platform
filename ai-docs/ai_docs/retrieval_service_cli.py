"""Command-line interface for SmartTouch documentation retrieval service."""

from __future__ import annotations

import argparse
import json
from typing import Any

from .retrieval_service import (
    answer_question,
    get_answer_context,
    search_documentation,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search SmartTouch documentation and print API-style JSON."
    )
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--model", default="text-embedding-3-small")
    parser.add_argument(
        "--format",
        choices=("search", "context", "answer"),
        default="search",
        help="Output the raw search response or citation-ready answer context.",
    )
    return parser

def run_search(
    argv: list[str] | argparse.Namespace | None = None,
    *,
    search_fn=search_documentation,
    answer_context_fn=get_answer_context,
    answer_question_fn=answer_question,
) -> dict:
    if isinstance(argv, argparse.Namespace):
        args = argv
    else:
        args = build_parser().parse_args(argv)

    if args.format == "answer":
        return answer_question_fn(
            args.query,
            limit=args.limit,
            model=args.model,
        )

    if args.format == "context":
        return answer_context_fn(
            args.query,
            limit=args.limit,
            model=args.model,
        )

    return search_fn(
        args.query,
        limit=args.limit,
        model=args.model,
    )

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    response = run_search(args)
    print(json.dumps(response, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
