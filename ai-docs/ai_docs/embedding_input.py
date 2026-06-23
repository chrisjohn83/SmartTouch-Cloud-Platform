"""Build provider-neutral text for document embeddings."""

from __future__ import annotations

from typing import Any


def _string_list(value: Any) -> list[str]:
    """Convert a metadata value into a clean list of strings."""

    if value is None:
        return []

    if isinstance(value, str):
        return [value.strip()] if value.strip() else []

    if isinstance(value, (list, tuple)):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    return [str(value).strip()]


def build_embedding_input(chunk: dict[str, Any]) -> str:
    """Create the text that an embedding model will receive."""

    title = str(chunk.get("title", "")).strip()
    content = str(chunk.get("content", "")).strip()

    heading_path = _string_list(chunk.get("heading_path"))
    section = " > ".join(heading_path)

    metadata = chunk.get("metadata") or {}
    questions = _string_list(
        metadata.get("ai-retrieval-questions")
    )
    tags = _string_list(metadata.get("tags"))
    tasks = _string_list(metadata.get("task"))

    parts: list[str] = []

    if title:
        parts.append(f"Document: {title}")

    if section:
        parts.append(f"Section: {section}")

    if tasks:
        parts.append(f"Tasks: {', '.join(tasks)}")

    if tags:
        parts.append(f"Topics: {', '.join(tags)}")

    if questions:
        formatted_questions = "\n".join(
            f"- {question}" for question in questions
        )
        parts.append(
            f"Related questions:\n{formatted_questions}"
        )

    if content:
        parts.append(f"Content:\n{content}")

    return "\n\n".join(parts)
