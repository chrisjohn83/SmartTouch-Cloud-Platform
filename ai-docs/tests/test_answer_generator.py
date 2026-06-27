from __future__ import annotations

import unittest

from ai_docs.answer_generator import generate_answer


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


class AnswerGeneratorTests(unittest.TestCase):
    def test_generates_answer_with_citations_and_sources(self) -> None:
        client = FakeAnswerClient(
            "Close the existing diagnostics session with "
            "`stctl remote-access close <session_id>` [source-1]."
        )
        answer_context = {
            "query": "A remote diagnostics session is already open",
            "contexts": [
                {
                    "citation_id": "source-1",
                    "title": "Common errors",
                    "heading": "Error: session already open",
                    "heading_label": (
                        "Common errors > Error: session already open"
                    ),
                    "source_path": "developers/onboarding/common-errors.md",
                    "source_url": "https://docs.example.com/common-errors/",
                    "excerpt": "Close the existing session.",
                }
            ],
        }

        response = generate_answer(
            answer_context,
            model_client=client,
        )

        self.assertEqual(
            response["query"],
            "A remote diagnostics session is already open",
        )
        self.assertIn("stctl remote-access close", response["answer"])
        self.assertEqual(response["citations"], ["source-1"])
        self.assertEqual(len(response["sources"]), 1)
        self.assertEqual(
            response["sources"][0]["source_url"],
            "https://docs.example.com/common-errors/",
        )
        self.assertEqual(len(client.calls), 1)
        self.assertIn("Use only the provided sources", client.calls[0]["system"])
        self.assertIn("[source-1]", client.calls[0]["user"])

    def test_deduplicates_citations(self) -> None:
        client = FakeAnswerClient(
            "Use the documented command [source-1]. Then retry [source-1]."
        )
        answer_context = {
            "query": "What should I do?",
            "contexts": [
                {
                    "citation_id": "source-1",
                    "title": "Common errors",
                }
            ],
        }

        response = generate_answer(answer_context, model_client=client)

        self.assertEqual(response["citations"], ["source-1"])

    def test_ignores_unknown_citations(self) -> None:
        client = FakeAnswerClient(
            "Use the documented command [source-99]."
        )
        answer_context = {
            "query": "What should I do?",
            "contexts": [
                {
                    "citation_id": "source-1",
                    "title": "Common errors",
                }
            ],
        }

        response = generate_answer(answer_context, model_client=client)

        self.assertEqual(response["citations"], ["source-99"])
        self.assertEqual(response["sources"], [])

    def test_returns_safe_answer_without_context(self) -> None:
        client = FakeAnswerClient("This should not be called.")
        answer_context = {
            "query": "Unknown question",
            "contexts": [],
        }

        response = generate_answer(answer_context, model_client=client)

        self.assertEqual(
            response["answer"],
            "The SmartTouch documentation does not provide enough "
            "information to answer this question.",
        )
        self.assertEqual(response["citations"], [])
        self.assertEqual(response["sources"], [])
        self.assertEqual(client.calls, [])


if __name__ == "__main__":
    unittest.main()
