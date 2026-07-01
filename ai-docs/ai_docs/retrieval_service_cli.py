"""Command-line interface for SmartTouch documentation retrieval service."""

from __future__ import annotations

import argparse
import json
from typing import Any

from .config import load_config

from .retrieval_service import (
    answer_question,
    get_answer_context,
    search_documentation,
)


def build_parser() -> argparse.ArgumentParser:
    config = load_config()
    parser = argparse.ArgumentParser(
        description="Search SmartTouch documentation and print API-style JSON."
    )
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=config.default_retrieval_limit)
    parser.add_argument("--model", default=config.embedding_model)
    parser.add_argument("--answer-model", default=config.answer_model)
    parser.add_argument(
        "--format",
        choices=("search", "context", "answer"),
        default="search",
        help="Output the raw search response or citation-ready answer context.",
    )
    parser.add_argument(
        "--use-knowledge-graph",
        action="store_true",
        help="Expand the query using build/kg-*.jsonl before retrieval.",
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
            answer_model=args.answer_model,
            use_knowledge_graph=args.use_knowledge_graph,
        )

    if args.format == "context":
        return answer_context_fn(
            args.query,
            limit=args.limit,
            model=args.model,
            use_knowledge_graph=args.use_knowledge_graph,
        )

    return search_fn(
        args.query,
        limit=args.limit,
        model=args.model,
        use_knowledge_graph=args.use_knowledge_graph,
    )

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    response = run_search(args)
    print(json.dumps(response, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
