"""Use knowledge graph relationships to expand documentation queries."""

from __future__ import annotations

from typing import Any


ALLOWED_EXPANSION_RELATIONSHIPS = {
    "connects_to",
    "uses",
}

CERTIFICATE_QUERY_TERMS = {
    "certificate",
    "cert",
    "tls",
    "expired",
    "expiry",
    "validation",
    "x509",
}


def expand_query_with_graph(
    query: str,
    graph: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Expand a query with directly connected concepts in the knowledge graph."""

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

    expanded_ids = _related_concept_ids(
        graph,
        matched_ids,
        concept_names=concept_names,
        normalized_query=normalized_query,
    )
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
    *,
    concept_names: dict[str, str],
    normalized_query: str,
) -> set[str]:
    related_ids: set[str] = set()

    for relationship in graph.get("relationships", []):
        relationship_type = str(relationship.get("type", ""))
        source_id = str(relationship.get("source_id", ""))
        target_id = str(relationship.get("target_id", ""))

        if relationship_type not in ALLOWED_EXPANSION_RELATIONSHIPS:
            continue

        if source_id in concept_ids and target_id.startswith("concept:"):
            _add_if_useful(
                related_ids,
                target_id,
                concept_names=concept_names,
                normalized_query=normalized_query,
            )

        if target_id in concept_ids and source_id.startswith("concept:"):
            _add_if_useful(
                related_ids,
                source_id,
                concept_names=concept_names,
                normalized_query=normalized_query,
            )

    return related_ids


def _add_if_useful(
    related_ids: set[str],
    concept_id: str,
    *,
    concept_names: dict[str, str],
    normalized_query: str,
) -> None:
    concept_name = concept_names.get(concept_id, "")

    if concept_name == "certificate" and not any(
        term in normalized_query for term in CERTIFICATE_QUERY_TERMS
    ):
        return

    related_ids.add(concept_id)
