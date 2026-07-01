"""Generate grounded answers from SmartTouch documentation context."""

from __future__ import annotations

import re
from typing import Any, Protocol
from .answer_prompt import build_answer_prompt


CITATION_RE = re.compile(r"\[(source-\d+)\]")

INSUFFICIENT_CITED_INFORMATION = (
    "The SmartTouch documentation does not provide enough cited "
    "information to answer this question."
)

FORBIDDEN_ANSWER_PHRASES = (
    "if you want",
    "i can help",
    "i can also",
)
def _contains_forbidden_phrase(answer: str) -> bool:
    normalized = answer.casefold()
    return any(phrase in normalized for phrase in FORBIDDEN_ANSWER_PHRASES)


class AnswerModelClient(Protocol):
    def generate(self, *, system: str, user: str) -> str:
        ...


def generate_answer(
    answer_context: dict[str, Any],
    *,
    model_client: AnswerModelClient,
) -> dict[str, Any]:
    """Generate a grounded answer from citation-ready context."""

    query = str(answer_context.get("query", "")).strip()
    contexts = answer_context.get("contexts") or []

    if not contexts:
        return _insufficient_response(query)

    prompt = build_answer_prompt(answer_context)

    def build_response(answer: str) -> dict[str, Any] | None:
        if _contains_forbidden_phrase(answer):
            return None

        citations = _extract_citations(answer)
        sources = _select_sources(contexts, citations)

        if not sources:
            return None

        return {
            "query": query,
            "answer": answer,
            "citations": [source["citation_id"] for source in sources],
            "sources": sources,
        }

    answer = model_client.generate(
        system=prompt["system"],
        user=prompt["user"],
    ).strip()

    response = build_response(answer)
    if response is not None:
        return response

    repair_user = (
        prompt["user"]
        + "\n\nThe previous answer was rejected because it did not use valid "
        "citations from the provided sources. Rewrite the answer using only "
        "the provided source IDs. Every factual sentence must include a valid "
        "citation. Do not add follow-up offers."
    )

    repaired_answer = model_client.generate(
        system=prompt["system"],
        user=repair_user,
    ).strip()

    response = build_response(repaired_answer)
    if response is not None:
        return response

    return _insufficient_response(query)

def _insufficient_response(query: str) -> dict[str, Any]:
    return {
        "query": query,
        "answer": INSUFFICIENT_CITED_INFORMATION,
        "citations": [],
        "sources": [],
    }

def _extract_citations(answer: str) -> list[str]:
    seen = set()
    citations = []

    for citation in CITATION_RE.findall(answer):
        if citation not in seen:
            citations.append(citation)
            seen.add(citation)

    return citations


def _select_sources(
    contexts: list[dict[str, Any]],
    citations: list[str],
) -> list[dict[str, Any]]:
    by_id = {
        context.get("citation_id"): context
        for context in contexts
    }

    sources = []
    for citation in citations:
        context = by_id.get(citation)
        if context is None:
            continue

        sources.append(
            {
                "citation_id": citation,
                "title": context.get("title"),
                "heading": context.get("heading"),
                "heading_label": context.get("heading_label"),
                "source_url": context.get("source_url"),
                "source_path": context.get("source_path"),
            }
        )

    return sources


def _insufficient_response(query: str) -> dict[str, Any]:
    """Return a standardized response when insufficient cited information.

    Includes the original query, a helpful answer message, and empty
    citations/sources lists so callers can rely on the response shape.
    """
    return {
        "query": query,
        "answer": INSUFFICIENT_CITED_INFORMATION,
        "citations": [],
        "sources": [],
    }
