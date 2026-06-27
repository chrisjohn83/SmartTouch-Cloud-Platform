"""Prompt builder for grounded SmartTouch documentation answers."""

from __future__ import annotations

from typing import Any


SYSTEM_INSTRUCTIONS = """You answer questions using only the provided SmartTouch documentation context.

Rules:
- Use only the provided sources.
- Cite every factual claim with source IDs like [source-1].
- If the sources do not contain enough information, say that the SmartTouch documentation does not provide enough information.
- Do not invent commands, URLs, product behavior, or configuration.
- Prefer concise, actionable answers.
"""


def build_answer_prompt(answer_context: dict[str, Any]) -> dict[str, str]:
    """Build a deterministic answer prompt from citation-ready context."""

    query = str(answer_context.get("query", "")).strip()
    contexts = answer_context.get("contexts") or []

    context_text = _format_contexts(contexts)

    user_prompt = f"""Question:
{query}

Sources:
{context_text}

Answer the question using only the sources above.
"""

    return {
        "system": SYSTEM_INSTRUCTIONS,
        "user": user_prompt,
    }


def _format_contexts(contexts: list[dict[str, Any]]) -> str:
    if not contexts:
        return "No sources were retrieved."

    blocks = []
    for context in contexts:
        citation_id = context.get("citation_id")
        title = context.get("title")
        heading_label = context.get("heading_label")
        source_url = context.get("source_url")
        excerpt = context.get("excerpt")

        blocks.append(
            f"""[{citation_id}]
Title: {title}
Heading: {heading_label}
URL: {source_url}
Excerpt:
{excerpt}"""
        )

    return "\n\n".join(blocks)
