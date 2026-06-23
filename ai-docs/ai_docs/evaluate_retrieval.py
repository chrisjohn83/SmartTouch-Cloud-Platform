"""Compare semantic and hybrid retrieval against SmartTouch evaluation cases."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .openai_embeddings import OpenAIEmbeddingProvider
from .search import load_records
from .semantic_search import normalize_text, rank_records, rank_records_hybrid


class QueryEmbeddingCache:
    """Persistent query-vector cache keyed by model and normalized query."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.entries: dict[str, list[float]] = {}
        if path.exists():
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError("Query embedding cache must contain a JSON object")
            self.entries = {
                str(key): [float(value) for value in vector]
                for key, vector in loaded.items()
            }

    @staticmethod
    def key(model: str, query: str) -> str:
        identity = f"{model}\0{normalize_text(query)}"
        return hashlib.sha256(identity.encode("utf-8")).hexdigest()

    def get_or_create(
        self,
        model: str,
        query: str,
        provider: OpenAIEmbeddingProvider | None = None,
    ) -> list[float]:
        key = self.key(model, query)
        if key not in self.entries:
            provider = provider or OpenAIEmbeddingProvider(model=model)
            self.entries[key] = provider.embed([query])[0].vector
            self._save()
        return self.entries[key]

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self.entries, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(self.path)


def find_expected_rank(
    ranked_records: list[dict[str, Any]],
    acceptable_paths: list[str],
    acceptable_sources: list[str],
) -> int | None:
    for rank, record in enumerate(ranked_records, start=1):
        heading_path = " > ".join(record["heading_path"])
        source_path = record["source_path"]
        path_match = any(
            value.casefold() in heading_path.casefold()
            for value in acceptable_paths
        )
        source_match = any(
            source_path.casefold().endswith(value.casefold())
            for value in acceptable_sources
        )
        if path_match or source_match:
            return rank
    return None


def _metrics(ranks: list[int | None]) -> tuple[float, float, float]:
    count = len(ranks)
    if count == 0:
        return 0.0, 0.0, 0.0
    top_1 = sum(rank == 1 for rank in ranks) / count
    top_3 = sum(rank is not None and rank <= 3 for rank in ranks) / count
    mrr = sum(1 / rank for rank in ranks if rank is not None) / count
    return top_1, top_3, mrr


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare SmartTouch semantic and hybrid retrieval."
    )
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--model", default="text-embedding-3-small")
    parser.add_argument("--search-limit", type=int, default=10)
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path("build/query-embedding-cache.json"),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    records = load_records(args.index)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    if not cases:
        print("No evaluation cases")
        return 2

    cache = QueryEmbeddingCache(args.cache)
    semantic_ranks: list[int | None] = []
    hybrid_ranks: list[int | None] = []

    for case in cases:
        query = case["query"]
        query_vector = cache.get_or_create(args.model, query)
        semantic = rank_records(
            query_vector,
            records,
            limit=args.search_limit,
        )
        hybrid = rank_records_hybrid(
            query,
            query_vector,
            records,
            limit=args.search_limit,
        )
        acceptable_paths = case.get("acceptable_paths", [])
        acceptable_sources = case.get("acceptable_sources", [])
        semantic_rank = find_expected_rank(
            [record for _, record in semantic],
            acceptable_paths,
            acceptable_sources,
        )
        hybrid_rank = find_expected_rank(
            [result.record for result in hybrid],
            acceptable_paths,
            acceptable_sources,
        )
        semantic_ranks.append(semantic_rank)
        hybrid_ranks.append(hybrid_rank)

        print(f"Query: {query}")
        print(
            f"Semantic rank: {semantic_rank or 'not found'} | "
            f"Hybrid rank: {hybrid_rank or 'not found'}"
        )
        for position, result in enumerate(hybrid[:5], start=1):
            heading = " > ".join(result.record["heading_path"])
            promotion = "/P" if result.lexical_promoted else ""
            print(
                f"  {position}. {result.final_score:.6f} - {heading} "
                f"[S{result.semantic_rank}/L{result.lexical_rank or '-'}"
                f"{promotion}]"
            )
        print()

    semantic_metrics = _metrics(semantic_ranks)
    hybrid_metrics = _metrics(hybrid_ranks)
    print(f"Cases: {len(cases)}")
    print(
        "Semantic - "
        f"Top-1: {semantic_metrics[0]:.2%}, "
        f"Top-3: {semantic_metrics[1]:.2%}, "
        f"MRR: {semantic_metrics[2]:.4f}"
    )
    print(
        "Hybrid   - "
        f"Top-1: {hybrid_metrics[0]:.2%}, "
        f"Top-3: {hybrid_metrics[1]:.2%}, "
        f"MRR: {hybrid_metrics[2]:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
