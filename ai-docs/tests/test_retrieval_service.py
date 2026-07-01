from __future__ import annotations

import os
import json
import tempfile
from pathlib import Path
import unittest
from dataclasses import dataclass
from unittest.mock import patch
from ai_docs.config import load_config

from ai_docs.retrieval_service import (
    RetrievalServiceError,
    answer_question,
    get_answer_context,
    search_documentation,
)


@dataclass
class FakeEmbedding:
    vector: list[float]


class FakeEmbeddingProvider:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[FakeEmbedding]:
        self.calls.append(texts)
        return [FakeEmbedding([0.1, 0.2, 0.3])]

class FakeAnswerClient:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.calls = []

    def generate(self, *, system: str, user: str) -> str:
        self.calls.append(
            {
                "system": system,
                "user": user,
            }
        )
        return self.answer

class RetrievalServiceTests(unittest.TestCase):
    def test_search_documentation_embeds_query_and_formats_response(self) -> None:
        provider = FakeEmbeddingProvider()
        search_calls = []

        def fake_search(
    query: str,
    vector: list[float],
    *,
    limit: int,
) -> list[dict]:
            # record the query and vector used by the search function
            search_calls.append((query, vector))
            return [
                {
                    "id": "chunk-1",
                    "title": "Common errors",
                    "heading": "Error: session already open",
                    "heading_path": [
                        "Common errors",
                        "Error: session already open",
                    ],
                    "source_path": "developers/onboarding/common-errors.md",
                    "source_url": "https://docs.example.com/common-errors/",
                    "content": "List and close the existing session.",
                    "metadata": {"persona": ["developer"]},
                    "final_score": 0.015,
                    "semantic_score": 0.552,
                    "lexical_score": 1.05,
                    "semantic_rank": 14,
                    "lexical_rank": 1,
                }
            ]
        response = search_documentation(
            "  A remote diagnostics session is already open  ",
            embedding_provider=provider,
            search_function=fake_search,
        )

        self.assertEqual(
            provider.calls,
            [["A remote diagnostics session is already open"]],
        )
        self.assertEqual(
            search_calls,
            [("A remote diagnostics session is already open", [0.1, 0.2, 0.3])],
        )
        self.assertEqual(
            response["query"],
            "A remote diagnostics session is already open",
        )
        self.assertEqual(response["result_count"], 1)
        self.assertEqual(response["results"][0]["id"], "chunk-1")
        self.assertEqual(response["results"][0]["scores"]["final"], 0.015)

    def test_search_documentation_can_expand_query_with_knowledge_graph(self) -> None:
        embedded_texts: list[str] = []
        search_queries: list[str] = []

        class FakeEmbeddingProvider:
            def embed(self, texts: list[str]):
                embedded_texts.extend(texts)

                class Result:
                    vector = [0.1, 0.2, 0.3]

                return [Result()]

        def fake_search(
            query: str,
            query_vector: list[float],
            *,
            limit: int,
        ):
            search_queries.append(query)
            return [
                {
                    "id": "chunk-1",
                    "title": "Connection errors",
                    "heading": "Broker connection failure",
                    "heading_path": ["Connection errors", "Broker connection failure"],
                    "source_path": "troubleshooting/connection.md",
                    "source_url": "https://docs.example.com/connection/",
                    "content": "Check broker connectivity and certificate validity.",
                    "metadata": {"persona": ["developer"]},
                    "final_score": 0.01,
                    "semantic_score": 0.5,
                    "lexical_score": 0.8,
                    "semantic_rank": 10,
                    "lexical_rank": 2,
                }
            ]

        knowledge_graph = {
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

        response = search_documentation(
            "device cannot connect to broker",
            limit=3,
            embedding_provider=FakeEmbeddingProvider(),
            search_function=fake_search,
            knowledge_graph=knowledge_graph,
        )

        self.assertEqual(response["query"], "device cannot connect to broker")
        self.assertEqual(
            embedded_texts,
            ["device cannot connect to broker agent certificate"],
        )
        self.assertEqual(
            search_queries,
            ["device cannot connect to broker agent certificate"],
        )

    def test_rejects_empty_query(self) -> None:
        with self.assertRaisesRegex(ValueError, "query is required"):
            search_documentation(
                "   ",
                embedding_provider=FakeEmbeddingProvider(),
                search_function=lambda query, vector, *, limit: [],
            )

    def test_rejects_invalid_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "limit must be at least 1"):
            search_documentation(
                "device offline",
                limit=0,
                embedding_provider=FakeEmbeddingProvider(),
                search_function=lambda query, vector: [],
            )

    def test_get_answer_context_uses_retrieval_response(self) -> None:
        provider = FakeEmbeddingProvider()

        def fake_search(query: str, vector: list[float], *, limit: int) -> list[dict]:
            return [
                {
                    "id": "chunk-1",
                    "title": "Common errors",
                    "heading": "Error: session already open",
                    "heading_path": [
                        "Common errors",
                        "Error: session already open",
                    ],
                    "source_path": "developers/onboarding/common-errors.md",
                    "source_url": "https://docs.example.com/common-errors/",
                    "content": "List and close the existing diagnostics session.",
                    "metadata": {"persona": ["developer"]},
                    "final_score": 0.015,
                    "semantic_score": 0.552,
                    "lexical_score": 1.05,
                    "semantic_rank": 14,
                    "lexical_rank": 1,
                }
            ]

        context = get_answer_context(
            "A remote diagnostics session is already open",
            embedding_provider=provider,
            search_function=fake_search,
            max_content_chars=20,
        )

        self.assertEqual(
            context["query"],
            "A remote diagnostics session is already open",
        )
        self.assertEqual(context["context_count"], 1)
        self.assertEqual(context["contexts"][0]["citation_id"], "source-1")
        self.assertEqual(
            context["contexts"][0]["heading_label"],
            "Common errors > Error: session already open",
        )
        self.assertEqual(context["contexts"][0]["excerpt"], "List and close the…")

    def test_wraps_dependency_failures(self) -> None:
        class FailingProvider:
            def embed(self, texts: list[str]) -> list[FakeEmbedding]:
                raise RuntimeError("boom")

        with self.assertRaisesRegex(
            RetrievalServiceError,
            "Retrieval service is unavailable",
        ):
            search_documentation(
                "device offline",
                embedding_provider=FailingProvider(),
                search_function=lambda query, vector: [],
            )

    def test_answer_question_retrieves_context_and_generates_answer(self) -> None:
        provider = FakeEmbeddingProvider()
        answer_client = FakeAnswerClient(
            "Close the existing diagnostics session [source-1]."
        )

        def fake_search(
            query: str,
            vector: list[float],
            *,
            limit: int,
        ) -> list[dict]:
            return [
                {
                    "id": "chunk-1",
                    "title": "Common errors",
                    "heading": "Error: session already open",
                    "heading_path": [
                        "Common errors",
                        "Error: session already open",
                    ],
                    "source_path": "developers/onboarding/common-errors.md",
                    "source_url": "https://docs.example.com/common-errors/",
                    "content": "List and close the existing diagnostics session.",
                    "metadata": {"persona": ["developer"]},
                    "final_score": 0.015,
                    "semantic_score": 0.552,
                    "lexical_score": 1.05,
                    "semantic_rank": 14,
                    "lexical_rank": 1,
                }
            ]

        response = answer_question(
            "A remote diagnostics session is already open",
            model_client=answer_client,
            embedding_provider=provider,
            search_function=fake_search,
        )

        self.assertEqual(
            response["query"],
            "A remote diagnostics session is already open",
        )
        self.assertEqual(
            response["answer"],
            "Close the existing diagnostics session [source-1].",
        )
        self.assertEqual(response["citations"], ["source-1"])
        self.assertEqual(len(response["sources"]), 1)
        self.assertEqual(
            response["sources"][0]["source_url"],
            "https://docs.example.com/common-errors/",
        )
        self.assertEqual(len(answer_client.calls), 1)

    def test_answer_question_wraps_answer_generation_failures(self) -> None:
        provider = FakeEmbeddingProvider()

        class FailingAnswerClient:
            def generate(self, *, system: str, user: str) -> str:
                raise RuntimeError("model failed")

        def fake_search(
            query: str,
            query_vector: list[float],
            *,
            limit: int,
        ):
            return [
                {
                    "id": "chunk-1",
                    "title": "Common errors",
                    "heading": "Error: session already open",
                    "heading_path": [
                        "Common errors",
                        "Error: session already open",
                    ],
                    "source_path": "developers/onboarding/common-errors.md",
                    "source_url": "https://example.com/common-errors",
                    "content": "Close the existing diagnostics session.",
                    "final_score": 0.015,
                    "semantic_score": 0.8,
                    "lexical_score": 0.2,
                    "semantic_rank": 1,
                    "lexical_rank": 1,
                }
            ]

        with self.assertRaisesRegex(
            RetrievalServiceError,
            "Answer generation service is unavailable",
        ):
            answer_question(
                "A remote diagnostics session is already open",
                model_client=FailingAnswerClient(),
                embedding_provider=provider,
                search_function=fake_search,
            )

    def test_search_documentation_uses_config_defaults(self) -> None:
        class FakeEmbeddingProvider:
            def __init__(self) -> None:
                self.model = None

            def embed(self, texts: list[str]):
                self.model = "not-used"
                return [type("Embedding", (), {"vector": [0.1] * 1536})()]

        def fake_search(
            query: str,
            query_vector: list[float],
            *,
            limit: int,
        ) -> list[dict]:
            return []

        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://configured",
                "AI_DOCS_EMBEDDING_MODEL": "configured-embedding-model",
            },
            clear=True,
        ):
            response = search_documentation(
                "device offline",
                embedding_provider=FakeEmbeddingProvider(),
                search_function=fake_search,
            )

        self.assertEqual(response["query"], "device offline")

    def test_search_documentation_can_load_knowledge_graph_from_store(self) -> None:
        embedded_texts: list[str] = []

        class FakeEmbeddingProvider:
            def embed(self, texts: list[str]):
                embedded_texts.extend(texts)

                class Result:
                    vector = [0.1, 0.2, 0.3]

                return [Result()]

        def fake_search(
            query: str,
            query_vector: list[float],
            *,
            limit: int,
        ) -> list[dict]:
            return []

        with tempfile.TemporaryDirectory() as temp_dir:
            graph_dir = Path(temp_dir)
            (graph_dir / "kg-entities.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "id": "concept:device",
                                "type": "concept",
                                "name": "device",
                            }
                        ),
                        json.dumps(
                            {
                                "id": "concept:broker",
                                "type": "concept",
                                "name": "broker",
                            }
                        ),
                        json.dumps(
                            {
                                "id": "concept:agent",
                                "type": "concept",
                                "name": "agent",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (graph_dir / "kg-relationships.jsonl").write_text(
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

            search_documentation(
                "device cannot connect to broker",
                embedding_provider=FakeEmbeddingProvider(),
                search_function=fake_search,
                use_knowledge_graph=True,
                knowledge_graph_dir=graph_dir,
            )

        self.assertEqual(
            embedded_texts,
            ["device cannot connect to broker agent"],
        )

if __name__ == "__main__":
    unittest.main()
