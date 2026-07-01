"""Prompt builder for grounded SmartTouch documentation answers."""

from __future__ import annotations

from typing import Any


SYSTEM_INSTRUCTIONS = """You answer SmartTouch documentation questions using only the provided sources.

Rules:
- Use only facts that appear in the provided sources.
- Every factual sentence must include a citation like [source-1].
- Do not add follow-up offers, suggestions, or conversational closing text.
- Do not say "I can help" or "If you want".
- If the sources do not contain enough information, say: The SmartTouch documentation does not provide enough cited information to answer this question.
- Preserve command examples exactly, including spaces, placeholders, flags, and line breaks.
- Put a space before each citation, for example: close the session. [source-1]
- Keep the answer concise and action-oriented.
- Use only these exact citation IDs: the source IDs shown in the context.
- Every paragraph must end with a valid citation.
- If you include a command block, cite the sentence before the command block and cite immediately after the command block.
- Do not cite sources that are not used in the answer."""


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
