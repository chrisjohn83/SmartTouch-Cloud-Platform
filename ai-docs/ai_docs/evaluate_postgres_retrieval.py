"""Evaluate PostgreSQL retrieval quality for SmartTouch documentation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from .evaluate_retrieval import find_expected_rank

from .openai_embeddings import OpenAIEmbeddingProvider
from .postgres_search import (
    database_url_from_environment,
    search_postgres,
    search_postgres_hybrid,
)

def load_cases(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        cases = json.load(file)

    if not isinstance(cases, list):
        raise ValueError("Evaluation fixture must contain a JSON array")

    return cases

class QueryEmbeddingCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.entries: dict[str, list[float]] = {}

        if path.is_file():
            with path.open(encoding="utf-8") as file:
                raw_entries = json.load(file)

            if isinstance(raw_entries, dict):
                self.entries = {
                    str(key): value
                    for key, value in raw_entries.items()
                    if isinstance(value, list)
                }

    def get_or_embed(
        self,
        *,
        model: str,
        query: str,
        provider: OpenAIEmbeddingProvider,
    ) -> list[float]:
        key = self._key(model, query)

        if key not in self.entries:
            self.entries[key] = provider.embed([query])[0].vector

        return self.entries[key]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(self.entries, file, indent=2, sort_keys=True)

    @staticmethod
    def _key(model: str, query: str) -> str:
        normalized_query = " ".join(query.casefold().split())
        return f"{model}:{normalized_query}"

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate PostgreSQL SmartTouch documentation retrieval."
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("tests/fixtures/retrieval-evaluation.json"),
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path("build/query-embedding-cache.json"),
    )
    parser.add_argument("--model", default="text-embedding-3-small")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--candidate-limit", type=int, default=50)
    return parser


def evaluate_mode(
    *,
    mode: str,
    cases: list[dict[str, Any]],
    query_vectors: dict[str, list[float]],
    database_url: str,
    limit: int,
    candidate_limit: int,
) -> dict[str, Any]:
    ranks: list[int | None] = []
    details: list[dict[str, Any]] = []

    for case in cases:
        query = case["query"]
        query_vector = query_vectors[query]

        if mode == "semantic":
            results = search_postgres(
                query_vector,
                database_url=database_url,
                limit=limit,
            )
        elif mode == "hybrid":
            results = search_postgres_hybrid(
                query,
                query_vector,
                database_url=database_url,
                limit=limit,
                candidate_limit=candidate_limit,
            )
        else:
            raise ValueError(f"Unsupported mode: {mode}")

        rank = find_expected_rank(
            results,
            case.get("acceptable_paths", []),
            case.get("acceptable_sources", []),
        )
        ranks.append(rank)

        details.append(
            {
                "query": query,
                "rank": rank,
                "results": results,
            }
        )

    total = len(cases)
    top_1 = sum(1 for rank in ranks if rank == 1)
    top_3 = sum(1 for rank in ranks if rank is not None and rank <= 3)
    reciprocal_sum = sum(1 / rank for rank in ranks if rank is not None)

    return {
        "mode": mode,
        "cases": total,
        "top_1_accuracy": top_1 / total if total else 0,
        "top_3_recall": top_3 / total if total else 0,
        "mrr": reciprocal_sum / total if total else 0,
        "details": details,
    }


def print_report(report: dict[str, Any]) -> None:
    print(f"\nMode: {report['mode']}")
    print(f"Cases: {report['cases']}")
    print(f"Top-1 accuracy: {report['top_1_accuracy']:.2%}")
    print(f"Top-3 recall: {report['top_3_recall']:.2%}")
    print(f"MRR: {report['mrr']:.4f}")

    for detail in report["details"]:
        rank = detail["rank"] if detail["rank"] is not None else "not found"
        print()
        print(f"Query: {detail['query']}")
        print(f"Expected rank: {rank}")

        for position, result in enumerate(detail["results"], start=1):
            heading_path = result.get("heading_path", [])
            heading = " > ".join(heading_path)
            score = result.get("final_score", result.get("score", 0))
            print(f"  {position}. {score:.4f} - {heading}")


def main() -> int:
    args = build_parser().parse_args()
    database_url = database_url_from_environment()

    cases = load_cases(args.cases)
    provider = OpenAIEmbeddingProvider(model=args.model)
    cache = QueryEmbeddingCache(args.cache)

    query_vectors: dict[str, list[float]] = {}
    for case in cases:
        query = case["query"]
        query_vectors[query] = cache.get_or_embed(
            model=args.model,
            query=query,
            provider=provider,
        )

    cache.save()

    semantic_report = evaluate_mode(
        mode="semantic",
        cases=cases,
        query_vectors=query_vectors,
        database_url=database_url,
        limit=args.limit,
        candidate_limit=args.candidate_limit,
    )
    hybrid_report = evaluate_mode(
        mode="hybrid",
        cases=cases,
        query_vectors=query_vectors,
        database_url=database_url,
        limit=args.limit,
        candidate_limit=args.candidate_limit,
    )

    print_report(semantic_report)
    print_report(hybrid_report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
