from __future__ import annotations

import unittest
from unittest.mock import patch

from ai_docs.http_api import (
    handle_answer_context_request,
    handle_search_request,
    health_response,
)


class HttpApiTests(unittest.TestCase):
    def test_health_response(self) -> None:
        self.assertEqual(
            health_response(),
            {
                "status": "ok",
                "service": "smarttouch-ai-docs",
            },
        )

    def test_handle_search_request_delegates_to_service(self) -> None:
        expected = {
            "query": "device offline",
            "result_count": 0,
            "results": [],
        }

        with patch(
            "ai_docs.http_api.search_documentation",
            return_value=expected,
        ) as search_documentation:
            response = handle_search_request(
                {
                    "query": " device offline ",
                    "limit": 3,
                }
            )

        self.assertEqual(response, expected)
        search_documentation.assert_called_once_with(
            "device offline",
            limit=3,
        )

    def test_handle_answer_context_request_delegates_to_service(self) -> None:
        expected = {
            "query": "device offline",
            "context_count": 0,
            "contexts": [],
        }

        with patch(
            "ai_docs.http_api.get_answer_context",
            return_value=expected,
        ) as get_answer_context:
            response = handle_answer_context_request(
                {
                    "query": " device offline ",
                    "limit": 3,
                    "max_content_chars": 500,
                }
            )

        self.assertEqual(response, expected)
        get_answer_context.assert_called_once_with(
            "device offline",
            limit=3,
            max_content_chars=500,
        )

    def test_rejects_missing_query(self) -> None:
        with self.assertRaisesRegex(ValueError, "query is required"):
            handle_search_request({"query": "   "})

    def test_rejects_invalid_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "limit must be at least 1"):
            handle_search_request(
                {
                    "query": "device offline",
                    "limit": 0,
                }
            )


if __name__ == "__main__":
    unittest.main()
