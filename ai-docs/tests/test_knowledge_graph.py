from __future__ import annotations

import unittest
import sys
import json
from pathlib import Path
from ai_docs.build_knowledge_graph import load_chunks, write_graph_jsonl
from ai_docs.knowledge_graph import extract_graph


ROOT_DIR = Path(__file__).resolve().parents[1]
while ROOT_DIR != ROOT_DIR.parent and not any(
    (ROOT_DIR / module).exists()
    for module in ("build_knowledge_graph.py", "knowledge_graph.py")
):
    ROOT_DIR = ROOT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class KnowledgeGraphTests(unittest.TestCase):
    def test_extracts_entities_from_chunk_metadata_and_content(self) -> None:
        chunks = [
            {
                "id": "chunk-1",
                "title": "Why is my device not connecting?",
                "heading": "Certificate error",
                "heading_path": [
                    "Why is my device not connecting?",
                    "Certificate error",
                    "Diagnosis method",
                ],
                "content": (
                    "The SmartTouch agent uses a device certificate to "
                    "connect to the broker. Run `stctl device agent-status`."
                ),
                "metadata": {
                    "product": ["remote-access"],
                    "task": ["troubleshooting", "device-connection"],
                    "tags": ["device", "certificate", "broker", "agent"],
                },
                "source_path": "developers/troubleshooting/why-device-not-connecting.md",
            }
        ]

        graph = extract_graph(chunks)

        entity_ids = {entity["id"] for entity in graph["entities"]}
        self.assertIn("concept:device", entity_ids)
        self.assertIn("concept:certificate", entity_ids)
        self.assertIn("concept:broker", entity_ids)
        self.assertIn("concept:agent", entity_ids)
        self.assertIn("command:stctl device agent-status", entity_ids)

        relationships = {
            (
                relationship["source_id"],
                relationship["type"],
                relationship["target_id"],
            )
            for relationship in graph["relationships"]
        }

        self.assertIn(
            ("chunk:chunk-1", "mentions", "concept:certificate"),
            relationships,
        )
        self.assertIn(
            ("chunk:chunk-1", "mentions", "command:stctl device agent-status"),
            relationships,
        )
    
    def test_extracts_typed_relationships_from_known_patterns(self) -> None:
        chunks = [
            {
                "id": "chunk-1",
                "title": "Device troubleshooting",
                "heading": "Certificate error",
                "heading_path": ["Device troubleshooting", "Certificate error"],
                "content": (
                    "The SmartTouch agent uses a device certificate to "
                    "connect to the broker."
                ),
                "metadata": {
                    "tags": ["agent", "certificate", "broker"],
                },
                "source_path": "developers/troubleshooting/device.md",
            }
        ]

        graph = extract_graph(chunks)

        relationships = {
            (
                relationship["source_id"],
                relationship["type"],
                relationship["target_id"],
            )
            for relationship in graph["relationships"]
        }

        self.assertIn(
            ("concept:agent", "uses", "concept:certificate"),
            relationships,
        )
        self.assertIn(
            ("concept:agent", "connects_to", "concept:broker"),
            relationships,
        )

    def test_deduplicates_entities_and_relationships(self) -> None:
        chunks = [
            {
                "id": "chunk-1",
                "title": "Device troubleshooting",
                "heading": "Quick diagnosis",
                "heading_path": ["Device troubleshooting", "Quick diagnosis"],
                "content": (
                    "Run `stctl device agent-status` to check the agent. "
                    "Run `stctl device agent-status` again after restart."
                ),
                "metadata": {
                    "tags": ["device", "agent", "device"],
                },
                "source_path": "developers/troubleshooting/device.md",
            }
        ]

        graph = extract_graph(chunks)

        entity_ids = [entity["id"] for entity in graph["entities"]]
        relationship_keys = [
            (
                relationship["source_id"],
                relationship["type"],
                relationship["target_id"],
            )
            for relationship in graph["relationships"]
        ]

        self.assertEqual(len(entity_ids), len(set(entity_ids)))
        self.assertEqual(len(relationship_keys), len(set(relationship_keys)))
    
    def test_writes_graph_jsonl_outputs(self) -> None:
        output_dir = Path("build/test-kg")
        chunks = [
            {
                "id": "chunk-1",
                "title": "Device troubleshooting",
                "heading": "Quick diagnosis",
                "heading_path": ["Device troubleshooting", "Quick diagnosis"],
                "content": "Run `stctl device agent-status` to check the agent.",
                "metadata": {"tags": ["device", "agent"]},
                "source_path": "developers/troubleshooting/device.md",
            }
        ]

        graph = extract_graph(chunks)
        counts = write_graph_jsonl(graph, output_dir)

        entities_path = output_dir / "kg-entities.jsonl"
        relationships_path = output_dir / "kg-relationships.jsonl"

        self.assertTrue(entities_path.is_file())
        self.assertTrue(relationships_path.is_file())
        self.assertEqual(counts["entities"], len(graph["entities"]))
        self.assertEqual(counts["relationships"], len(graph["relationships"]))

        first_entity = json.loads(
            entities_path.read_text(encoding="utf-8").splitlines()[0]
        )
        self.assertIn("id", first_entity)

if __name__ == "__main__":
    unittest.main()
