"""Rank embedded documentation chunks by semantic and lexical relevance."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Any, Sequence

TOKEN_RE = re.compile(r"[a-z0-9]+(?:[._-][a-z0-9]+)*")
FIELD_WEIGHTS = {
    "title": 1.5,
    "heading": 4.0,
    "content": 1.0,
    "questions": 2.0,
}
PHRASE_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "been",
    "being",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "how",
    "i",
    "is",
    "me",
    "my",
    "of",
    "or",
    "the",
    "to",
    "was",
    "were",
    "why",
    "with",
    "your",
}


@dataclass(frozen=True)
class HybridSearchResult:
    """One hybrid result with enough detail to diagnose ranking behavior."""

    final_score: float
    semantic_score: float
    lexical_score: float
    semantic_rank: int
    lexical_rank: int | None
    lexical_promoted: bool
    record: dict[str, Any]


def normalize_text(text: str) -> str:
    """Normalize punctuation and Unicode while preserving command-like tokens."""

    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = normalized.replace("’", "'").replace("`", "'")
    normalized = re.sub(r"(?<=\w)'(?=\w)", "", normalized)
    return " ".join(TOKEN_RE.findall(normalized))


def tokenize(text: str) -> list[str]:
    """Return normalized lexical tokens."""

    normalized = normalize_text(text)
    return normalized.split() if normalized else []


def longest_heading_phrase(query: str, heading: str) -> int:
    """Return the longest contiguous meaningful token phrase shared by both."""

    query_tokens = [
        token for token in tokenize(query) if token not in PHRASE_STOP_WORDS
    ]
    heading_tokens = [
        token for token in tokenize(heading) if token not in PHRASE_STOP_WORDS
    ]
    longest = 0

    for query_index in range(len(query_tokens)):
        for heading_index in range(len(heading_tokens)):
            length = 0
            while (
                query_index + length < len(query_tokens)
                and heading_index + length < len(heading_tokens)
                and query_tokens[query_index + length]
                == heading_tokens[heading_index + length]
            ):
                length += 1
            longest = max(longest, length)

    return longest


def cosine_similarity(
    left: Sequence[float],
    right: Sequence[float],
) -> float:
    if len(left) != len(right):
        raise ValueError("Vectors must have equal dimensions")
    if not left:
        raise ValueError("Vectors cannot be empty")

    dot_product = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))

    if left_norm == 0 or right_norm == 0:
        raise ValueError("Vectors cannot have zero magnitude")

    return dot_product / (left_norm * right_norm)


def rank_records(
    query_vector: Sequence[float],
    records: Sequence[dict[str, Any]],
    limit: int = 5,
) -> list[tuple[float, dict[str, Any]]]:
    """Rank records using cosine similarity only."""

    if limit < 1:
        raise ValueError("Limit must be at least 1")

    scored = [
        (
            cosine_similarity(query_vector, record["embedding"]["vector"]),
            record,
        )
        for record in records
    ]
    return sorted(scored, key=lambda item: item[0], reverse=True)[:limit]


def _metadata_strings(record: dict[str, Any], key: str) -> list[str]:
    value = (record.get("metadata") or {}).get(key, [])
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _record_fields(record: dict[str, Any]) -> dict[str, str]:
    return {
        "title": str(record.get("title") or ""),
        "heading": " > ".join(str(item) for item in record.get("heading_path", [])),
        "content": str(record.get("content") or ""),
        "questions": " ".join(_metadata_strings(record, "ai-retrieval-questions")),
    }


def lexical_scores(
    query: str,
    records: Sequence[dict[str, Any]],
    *,
    k1: float = 1.2,
    b: float = 0.75,
) -> list[float]:
    """Calculate field-weighted BM25-style scores for every record."""

    query_tokens = tokenize(query)
    if not query_tokens:
        return [0.0] * len(records)

    tokenized_records = [
        {
            field: tokenize(text)
            for field, text in _record_fields(record).items()
        }
        for record in records
    ]
    document_count = len(records)
    document_frequency: Counter[str] = Counter()

    for fields in tokenized_records:
        present = set().union(*(set(tokens) for tokens in fields.values()))
        document_frequency.update(present)

    average_lengths = {
        field: (
            sum(len(fields[field]) for fields in tokenized_records) / document_count
            if document_count
            else 0.0
        )
        for field in FIELD_WEIGHTS
    }

    scores: list[float] = []
    normalized_query = normalize_text(query)
    query_token_set = set(query_tokens)

    for record, fields in zip(records, tokenized_records):
        score = 0.0
        for field, weight in FIELD_WEIGHTS.items():
            tokens = fields[field]
            frequencies = Counter(tokens)
            average_length = average_lengths[field] or 1.0
            length_normalizer = 1.0 - b + b * len(tokens) / average_length

            for token in query_tokens:
                frequency = frequencies[token]
                if frequency == 0:
                    continue
                frequency_weight = (
                    frequency * (k1 + 1.0)
                    / (frequency + k1 * length_normalizer)
                )
                frequency_in_docs = document_frequency[token]
                inverse_document_frequency = math.log(
                    1.0
                    + (
                        document_count - frequency_in_docs + 0.5
                    )
                    / (frequency_in_docs + 0.5)
                )
                score += weight * inverse_document_frequency * frequency_weight

        normalized_heading = normalize_text(_record_fields(record)["heading"])
        heading_tokens = set(fields["heading"])
        if normalized_query and normalized_query in normalized_heading:
            score += 8.0
        elif query_token_set:
            heading_coverage = len(query_token_set & heading_tokens) / len(query_token_set)
            score += 4.0 * heading_coverage * heading_coverage

        scores.append(score)

    return scores


def rank_records_hybrid(
    query: str,
    query_vector: Sequence[float],
    records: Sequence[dict[str, Any]],
    limit: int = 5,
    *,
    rrf_k: int = 60,
    semantic_weight: float = 1.0,
    lexical_weight: float = 0.01,
) -> list[HybridSearchResult]:
    """Fuse ranks conservatively and promote strong operational heading phrases."""

    if limit < 1:
        raise ValueError("Limit must be at least 1")
    if rrf_k < 1:
        raise ValueError("rrf_k must be at least 1")

    semantic_scored = [
        (
            cosine_similarity(query_vector, record["embedding"]["vector"]),
            index,
        )
        for index, record in enumerate(records)
    ]
    semantic_scored.sort(key=lambda item: (-item[0], item[1]))
    semantic_rank = {
        index: rank
        for rank, (_, index) in enumerate(semantic_scored, start=1)
    }
    semantic_score = {index: score for score, index in semantic_scored}

    raw_lexical_scores = lexical_scores(query, records)
    lexical_scored = [
        (score, index)
        for index, score in enumerate(raw_lexical_scores)
        if score > 0.0
    ]
    lexical_scored.sort(key=lambda item: (-item[0], item[1]))
    lexical_rank = {
        index: rank
        for rank, (_, index) in enumerate(lexical_scored, start=1)
    }

    results: list[HybridSearchResult] = []
    for index, record in enumerate(records):
        final_score = semantic_weight / (rrf_k + semantic_rank[index])
        current_lexical_rank = lexical_rank.get(index)
        if current_lexical_rank is not None:
            final_score += lexical_weight / (rrf_k + current_lexical_rank)

        results.append(
            HybridSearchResult(
                final_score=final_score,
                semantic_score=semantic_score[index],
                lexical_score=raw_lexical_scores[index],
                semantic_rank=semantic_rank[index],
                lexical_rank=current_lexical_rank,
                lexical_promoted=False,
                record=record,
            )
        )

    ranked = sorted(
        results,
        key=lambda item: (
            -item.final_score,
            -item.semantic_score,
            str(item.record.get("id", "")),
        ),
    )

    # A strong phrase in the lexical leader usually represents an exact command
    # or operational error. Put it at rank 2 without displacing the best
    # semantic result or letting broad keyword matches reshape the whole list.
    if lexical_scored and len(ranked) > 1:
        lexical_leader_index = lexical_scored[0][1]
        lexical_leader = next(
            result
            for result in ranked
            if result.record is records[lexical_leader_index]
        )
        heading = _record_fields(lexical_leader.record)["heading"]
        if (
            longest_heading_phrase(query, heading) >= 3
            and ranked.index(lexical_leader) > 1
        ):
            ranked.remove(lexical_leader)
            promoted_score = (ranked[0].final_score + ranked[1].final_score) / 2
            promoted = HybridSearchResult(
                final_score=promoted_score,
                semantic_score=lexical_leader.semantic_score,
                lexical_score=lexical_leader.lexical_score,
                semantic_rank=lexical_leader.semantic_rank,
                lexical_rank=lexical_leader.lexical_rank,
                lexical_promoted=True,
                record=lexical_leader.record,
            )
            ranked.insert(1, promoted)

    return ranked[:limit]
