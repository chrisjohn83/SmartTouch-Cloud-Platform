"""Use knowledge graph relationships to expand documentation queries."""

from __future__ import annotations

from typing import Any

def expand_query_with_graph(
    query: str,
    graph: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Expand a query with concepts connected in the knowledge graph."""

    normalized_query = query.casefold()
    concept_names = _concept_names_by_id(graph)

    matched_ids = {
        entity_id
        for entity_id, name in concept_names.items()
        if _term_matches_query(name, normalized_query)
    }

    matched_terms = sorted(
        concept_names[entity_id]
        for entity_id in matched_ids
    )

    first_hop_ids = _related_concept_ids(graph, matched_ids)
    second_hop_ids = _related_concept_ids(graph, first_hop_ids)

    expanded_ids = set()
    expanded_ids.update(first_hop_ids)
    expanded_ids.update(second_hop_ids)
    expanded_ids.difference_update(matched_ids)

    expanded_terms = sorted(
        concept_names[entity_id]
        for entity_id in expanded_ids
        if entity_id in concept_names
        and concept_names[entity_id] not in matched_terms
    )

    expanded_query = " ".join([query, *expanded_terms]).strip()

    return {
        "query": query,
        "expanded_query": expanded_query,
        "matched_terms": matched_terms,
        "expanded_terms": expanded_terms,
    }

def _concept_names_by_id(
    graph: dict[str, list[dict[str, Any]]],
) -> dict[str, str]:
    concepts = {}

    for entity in graph.get("entities", []):
        if entity.get("type") != "concept":
            continue

        entity_id = str(entity.get("id", ""))
        name = str(entity.get("name", "")).strip().casefold()

        if entity_id and name:
            concepts[entity_id] = name

    return concepts

def _term_matches_query(term: str, normalized_query: str) -> bool:
    return term in normalized_query

def _related_concept_ids(
    graph: dict[str, list[dict[str, Any]]],
    concept_ids: set[str],
) -> set[str]:
    related_ids: set[str] = set()

    for relationship in graph.get("relationships", []):
        source_id = str(relationship.get("source_id", ""))
        target_id = str(relationship.get("target_id", ""))

        if source_id in concept_ids and target_id.startswith("concept:"):
            related_ids.add(target_id)

        if target_id in concept_ids and source_id.startswith("concept:"):
            related_ids.add(source_id)

    return related_ids