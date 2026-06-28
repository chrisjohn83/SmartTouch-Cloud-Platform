from __future__ import annotations

import argparse
import unittest

import os
from unittest.mock import patch

from ai_docs.retrieval_service_cli import build_parser, run_search


class RetrievalServiceCliTests(unittest.TestCase):
    def test_parser_accepts_query_limit_and_model(self) -> None:
        args = build_parser().parse_args(
            [
                "--query",
                "device offline",
                "--limit",
                "3",
                "--model",
                "text-embedding-3-small",
                "--format",
                "context",
            ]
        )

        self.assertEqual(args.query, "device offline")
        self.assertEqual(args.limit, 3)
        self.assertEqual(args.model, "text-embedding-3-small")
        self.assertEqual(args.format, "context")

    def test_run_search_delegates_to_service(self) -> None:
        args = argparse.Namespace(
            query="device offline",
            limit=3,
            model="text-embedding-3-small",
            format="search",
        )

        expected = {
            "query": "device offline",
            "result_count": 0,
            "results": [],
        }

        def fake_search(query: str, *, limit: int, model: str) -> dict:
            self.assertEqual(query, "device offline")
            self.assertEqual(limit, 3)
            self.assertEqual(model, "text-embedding-3-small")
            return expected

        response = run_search(args, search_fn=fake_search)

        self.assertEqual(response, expected)

    def test_run_search_can_return_answer_context(self) -> None:
        args = argparse.Namespace(
            query="device offline",
            limit=3,
            model="text-embedding-3-small",
            format="context",
        )

        expected = {
            "query": "device offline",
            "context_count": 0,
            "contexts": [],
        }

        def fake_answer_context(query: str, *, limit: int, model: str) -> dict:
            self.assertEqual(query, "device offline")
            self.assertEqual(limit, 3)
            self.assertEqual(model, "text-embedding-3-small")
            return expected

        response = run_search(args, answer_context_fn=fake_answer_context)

        self.assertEqual(response, expected)

    def test_run_search_can_return_answer(self) -> None:
        expected = {
            "query": "test",
            "answer": "Use the documented command. [source-1]",
            "citations": ["source-1"],
            "sources": [{"citation_id": "source-1"}],
        }

        def fake_answer_question(query: str, *, limit: int, model: str, answer_model: str,) -> dict:
            self.assertEqual(query, "test")
            self.assertEqual(limit, 3)
            self.assertEqual(model, "gpt-5.4-mini")
            return expected

        args = build_parser().parse_args(
            [
                "--query",
                "test",
                "--limit",
                "3",
                "--model",
                "gpt-5.4-mini",
                "--format",
                "answer",
            ]
        )

        response = run_search(args, answer_question_fn=fake_answer_question)

        self.assertEqual(response, expected)

def test_parser_uses_config_defaults(self) -> None:
    with patch.dict(
        os.environ,
        {
            "AI_DOCS_DEFAULT_RETRIEVAL_LIMIT": "7",
            "AI_DOCS_EMBEDDING_MODEL": "configured-embedding",
            "AI_DOCS_ANSWER_MODEL": "configured-answer",
        },
        clear=True,
    ):
        args = build_parser().parse_args(
            [
                "--query",
                "device offline",
            ]
        )

    self.assertEqual(args.limit, 7)
    self.assertEqual(args.model, "configured-embedding")
    self.assertEqual(args.answer_model, "configured-answer")


if __name__ == "__main__":
    unittest.main()
