"""Generate grounded answers from SmartTouch documentation context."""

from __future__ import annotations

import re
from typing import Any, Protocol

from .answer_prompt import build_answer_prompt


CITATION_RE = re.compile(r"\[(source-\d+)\]")


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
        return {
            "query": query,
            "answer": (
                "The SmartTouch documentation does not provide enough "
                "information to answer this question."
            ),
            "citations": [],
            "sources": [],
        }

    prompt = build_answer_prompt(answer_context)
    answer = model_client.generate(
        system=prompt["system"],
        user=prompt["user"],
    ).strip()

    citations = _extract_citations(answer)
    sources = _select_sources(contexts, citations)

    return {
        "query": query,
        "answer": answer,
        "citations": citations,
        "sources": sources,
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
