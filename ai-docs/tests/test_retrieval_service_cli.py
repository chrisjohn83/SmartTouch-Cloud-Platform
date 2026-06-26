from __future__ import annotations

import argparse
import unittest
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

        with patch(
            "ai_docs.retrieval_service_cli.search_documentation",
            return_value=expected,
        ) as search_documentation:
            response = run_search(args)

        self.assertEqual(response, expected)
        search_documentation.assert_called_once_with(
            "device offline",
            limit=3,
            model="text-embedding-3-small",
        )

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

        with patch(
            "ai_docs.retrieval_service_cli.get_answer_context",
            return_value=expected,
        ) as get_answer_context:
            response = run_search(args)

        self.assertEqual(response, expected)
        get_answer_context.assert_called_once_with(
            "device offline",
            limit=3,
            model="text-embedding-3-small",
        )


if __name__ == "__main__":
    unittest.main()
