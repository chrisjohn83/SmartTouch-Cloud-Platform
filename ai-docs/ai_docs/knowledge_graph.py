"""Extract a lightweight knowledge graph from documentation chunks."""

from __future__ import annotations

import re
from typing import Any


COMMAND_RE = re.compile(r"`([^`]+)`")


def extract_graph(chunks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Extract entities and relationships from documentation chunks."""

    entities_by_id: dict[str, dict[str, Any]] = {}
    relationships_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}

    def add_entity(entity: dict[str, Any]) -> None:
        entities_by_id.setdefault(entity["id"], entity)

    def add_relationship(
        source_id: str,
        relationship_type: str,
        target_id: str,
        *,
        chunk_id: str,
    ) -> None:
        key = (source_id, relationship_type, target_id)
        relationships_by_key.setdefault(
            key,
            {
                "source_id": source_id,
                "type": relationship_type,
                "target_id": target_id,
                "chunk_id": chunk_id,
            },
        )

    for chunk in chunks:
        chunk_id = str(chunk["id"])
        chunk_entity_id = f"chunk:{chunk_id}"

        add_entity(
            {
                "id": chunk_entity_id,
                "type": "chunk",
                "name": str(chunk.get("heading") or chunk.get("title") or chunk_id),
                "source_path": chunk.get("source_path"),
                "chunk_id": chunk_id,
            }
        )

        concepts = _concepts_from_chunk(chunk)
        for concept in concepts:
            concept_id = f"concept:{concept}"
            add_entity(
                {
                    "id": concept_id,
                    "type": "concept",
                    "name": concept,
                }
            )
            add_relationship(
                chunk_entity_id,
                "mentions",
                concept_id,
                chunk_id=chunk_id,
            )
        
        for source_id, relationship_type, target_id in _typed_relationships_from_content(
            str(chunk.get("content", ""))
        ):
            add_relationship(
                source_id,
                relationship_type,
                target_id,
                chunk_id=chunk_id,
            )

        for command in _commands_from_content(str(chunk.get("content", ""))):
            command_id = f"command:{command}"
            add_entity(
                {
                    "id": command_id,
                    "type": "command",
                    "name": command,
                }
            )
            add_relationship(
                chunk_entity_id,
                "mentions",
                command_id,
                chunk_id=chunk_id,
            )

    return {
        "entities": list(entities_by_id.values()),
        "relationships": list(relationships_by_key.values()),
    }


def _concepts_from_chunk(chunk: dict[str, Any]) -> list[str]:
    metadata = chunk.get("metadata") or {}
    values: list[str] = []

    for field in ("product", "task", "tags"):
        raw_value = metadata.get(field)
        if isinstance(raw_value, list):
            values.extend(str(value) for value in raw_value)
        elif raw_value:
            values.append(str(raw_value))

    text = " ".join(
        [
            str(chunk.get("title", "")),
            str(chunk.get("heading", "")),
            " ".join(str(value) for value in chunk.get("heading_path", [])),
            str(chunk.get("content", "")),
        ]
    ).casefold()

    known_terms = (
        "device",
        "certificate",
        "broker",
        "agent",
        "remote-access",
        "troubleshooting",
        "device-connection",
    )

    for term in known_terms:
        if term in text:
            values.append(term)

    return sorted({_normalize_concept(value) for value in values if value})


def _commands_from_content(content: str) -> list[str]:
    commands = []

    for inline in COMMAND_RE.findall(content):
        command = inline.strip()
        if command.startswith("stctl "):
            commands.append(command)

    return sorted(set(commands))


def _typed_relationships_from_content(content: str) -> list[tuple[str, str, str]]:
    """Extract typed relationships from content.

    This is a lightweight fallback implementation that currently does not
    attempt complex NLP — it returns an empty list. Implement more
    sophisticated extraction later if needed.
    """
    return []

def _typed_relationships_from_content(content: str) -> list[tuple[str, str, str]]:
    text = content.casefold()
    relationships: list[tuple[str, str, str]] = []

    if (
        "agent" in text
        and "certificate" in text
        and ("uses" in text or "use" in text)
    ):
        relationships.append(
            ("concept:agent", "uses", "concept:certificate")
        )

    if (
        "agent" in text
        and "broker" in text
        and ("connect to" in text or "connects to" in text)
    ):
        relationships.append(
            ("concept:agent", "connects_to", "concept:broker")
        )

    return relationships

def _normalize_concept(value: str) -> str:
    return value.strip().casefold().replace("_", "-")
