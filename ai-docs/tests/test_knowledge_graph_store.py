from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from ai_docs.retrieval_service import search_documentation
from ai_docs.knowledge_graph_store import load_knowledge_graph


class KnowledgeGraphStoreTests(unittest.TestCase):
    def test_loads_graph_from_jsonl_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            graph_dir = Path(temp_dir)

            entities_path = graph_dir / "kg-entities.jsonl"
            relationships_path = graph_dir / "kg-relationships.jsonl"

            entities_path.write_text(
                json.dumps(
                    {
                        "id": "concept:broker",
                        "type": "concept",
                        "name": "broker",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            relationships_path.write_text(
                json.dumps(
                    {
                        "source_id": "concept:agent",
                        "target_id": "concept:broker",
                        "type": "connects_to",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            graph = load_knowledge_graph(graph_dir)

        self.assertEqual(
            graph,
            {
                "entities": [
                    {
                        "id": "concept:broker",
                        "type": "concept",
                        "name": "broker",
                    }
                ],
                "relationships": [
                    {
                        "source_id": "concept:agent",
                        "target_id": "concept:broker",
                        "type": "connects_to",
                    }
                ],
            },
        )

    def test_returns_none_when_graph_files_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            graph = load_knowledge_graph(Path(temp_dir))

        self.assertIsNone(graph)

    def test_rejects_invalid_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            graph_dir = Path(temp_dir)
            (graph_dir / "kg-entities.jsonl").write_text(
                "{not json}\n",
                encoding="utf-8",
            )
            (graph_dir / "kg-relationships.jsonl").write_text(
                "",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Invalid JSON"):
                load_knowledge_graph(graph_dir)


if __name__ == "__main__":
    unittest.main()
