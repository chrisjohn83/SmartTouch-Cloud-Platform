from __future__ import annotations

import unittest
from dataclasses import dataclass

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

        def fake_search(query: str, vector: list[float]) -> list[dict]:
            search_calls.append((query, vector))
            return [
                {
                    "id": "chunk-1",
                    "title": "Common errors",
                    "heading": "Error: session already open",
                    "heading_path": ["Common errors", "Error: session already open"],
                    "source_path": "developers/onboarding/common-errors.md",
                    "source_url": "https://docs.example.com/common-errors/",
                    "content": "Close the existing session.",
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

    def test_rejects_empty_query(self) -> None:
        with self.assertRaisesRegex(ValueError, "query must not be empty"):
            search_documentation(
                "   ",
                embedding_provider=FakeEmbeddingProvider(),
                search_function=lambda query, vector: [],
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

        def fake_search(query: str, vector: list[float]) -> list[dict]:
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

        def fake_search(query: str, vector: list[float]) -> list[dict]:
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

if __name__ == "__main__":
    unittest.main()
