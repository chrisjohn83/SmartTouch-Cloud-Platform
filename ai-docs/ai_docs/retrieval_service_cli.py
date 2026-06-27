"""Command-line interface for SmartTouch documentation retrieval service."""

from __future__ import annotations

import argparse
import json
from typing import Any

from .retrieval_service import get_answer_context, search_documentation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search SmartTouch documentation and print API-style JSON."
    )
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--model", default="text-embedding-3-small")
    parser.add_argument(
        "--format",
        choices=("search", "context"),
        default="search",
        help="Output the raw search response or citation-ready answer context.",
    )
    return parser


def run_search(args: argparse.Namespace) -> dict[str, Any]:
    if args.format == "context":
        return get_answer_context(
            args.query,
            limit=args.limit,
            model=args.model,
        )
    return search_documentation(
        args.query,
        limit=args.limit,
        model=args.model,
    )


def main() -> int:
    args = build_parser().parse_args()
    response = run_search(args)
    print(json.dumps(response, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
