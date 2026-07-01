from __future__ import annotations

import unittest

from ai_docs.knowledge_graph_query import expand_query_with_graph


class KnowledgeGraphQueryTests(unittest.TestCase):
    def test_expands_query_with_related_graph_concepts(self) -> None:
        graph = {
            "entities": [
                {"id": "concept:agent", "type": "concept", "name": "agent"},
                {"id": "concept:broker", "type": "concept", "name": "broker"},
                {"id": "concept:certificate", "type": "concept", "name": "certificate"},
                {"id": "concept:device", "type": "concept", "name": "device"},
            ],
            "relationships": [
                {
                    "source_id": "concept:agent",
                    "type": "connects_to",
                    "target_id": "concept:broker",
                    "chunk_id": "chunk-1",
                },
                {
                    "source_id": "concept:agent",
                    "type": "uses",
                    "target_id": "concept:certificate",
                    "chunk_id": "chunk-1",
                },
            ],
        }

        result = expand_query_with_graph(
            "device cannot connect to broker",
            graph,
        )

        self.assertEqual(
            result["expanded_query"],
            "device cannot connect to broker agent",
        )
        self.assertEqual(
            result["matched_terms"],
            ["broker", "device"],
        )
        self.assertEqual(
            result["expanded_terms"],
            ["agent"],
        )

    def test_expands_certificate_when_query_mentions_certificate(self) -> None:
        graph = {
            "entities": [
                {"id": "concept:agent", "type": "concept", "name": "agent"},
                {"id": "concept:certificate", "type": "concept", "name": "certificate"},
            ],
            "relationships": [
                {
                    "source_id": "concept:agent",
                    "type": "uses",
                    "target_id": "concept:certificate",
                    "chunk_id": "chunk-1",
                }
            ],
        }

        result = expand_query_with_graph(
            "agent certificate expired",
            graph,
        )

        self.assertEqual(
            result["expanded_query"],
            "agent certificate expired",
        )
        self.assertEqual(result["matched_terms"], ["agent", "certificate"])
        self.assertEqual(result["expanded_terms"], [])

    def test_leaves_query_unchanged_without_graph_matches(self) -> None:
        graph = {
            "entities": [
                {"id": "concept:agent", "type": "concept", "name": "agent"},
                {"id": "concept:broker", "type": "concept", "name": "broker"},
            ],
            "relationships": [
                {
                    "source_id": "concept:agent",
                    "type": "connects_to",
                    "target_id": "concept:broker",
                    "chunk_id": "chunk-1",
                }
            ],
        }

        result = expand_query_with_graph(
            "how do I deploy a service",
            graph,
        )

        self.assertEqual(result["expanded_query"], "how do I deploy a service")
        self.assertEqual(result["matched_terms"], [])
        self.assertEqual(result["expanded_terms"], [])


if __name__ == "__main__":
    unittest.main()
