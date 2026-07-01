from __future__ import annotations

import unittest
from unittest.mock import patch
import os
from typing import Any
from ai_docs.http_api import (
    handle_answer_context_request,
    handle_answer_request,
    handle_search_request,
    health_response,
    diagnostics_response,
)
from ai_docs.config import load_config


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
                    "use_knowledge_graph": True,
                }
            )

        self.assertEqual(response, expected)
        search_documentation.assert_called_once_with(
            "device offline",
            limit=3,
            model="text-embedding-3-small",
            use_knowledge_graph=True,
        )

    def test_search_request_disables_knowledge_graph_by_default(self) -> None:
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
                    "query": "device offline",
                    "limit": 3,
                }
            )

        self.assertEqual(response, expected)
        search_documentation.assert_called_once_with(
            "device offline",
            limit=3,
            model="text-embedding-3-small",
            use_knowledge_graph=False,
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
                    "use_knowledge_graph": True,
                }
            )

        self.assertEqual(response, expected)
        get_answer_context.assert_called_once_with(
            "device offline",
            limit=3,
            model="text-embedding-3-small",
            max_content_chars=500,
            use_knowledge_graph=True,
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

    def test_handle_answer_request_delegates_to_service(self) -> None:
        expected = {
            "query": "device offline",
            "answer": "Restart the agent [source-1].",
            "citations": ["source-1"],
            "sources": [],
        }

        with patch(
            "ai_docs.http_api.answer_question",
            return_value=expected,
        ) as answer_question:
            response = handle_answer_request(
                {
                    "query": " device offline ",
                    "limit": 3,
                    "answer_model": "gpt-5.4-mini",
                    "use_knowledge_graph": True,
                }
            )

        self.assertEqual(response, expected)
        answer_question.assert_called_once_with(
            "device offline",
            limit=3,
            model="text-embedding-3-small",
            answer_model="gpt-5.4-mini",
            max_content_chars=1200,
            use_knowledge_graph=True,
        )

def test_search_request_uses_config_defaults(self) -> None:
    expected = {"query": "device offline", "result_count": 0, "results": []}

    with patch.dict(
        os.environ,
        {
            "AI_DOCS_DEFAULT_RETRIEVAL_LIMIT": "7",
            "AI_DOCS_EMBEDDING_MODEL": "configured-embedding",
        },
        clear=True,
    ):
        with patch(
            "ai_docs.http_api.search_documentation",
            return_value=expected,
        ) as search_documentation:
            response = handle_search_request(
                {"query": "device offline"}
            )

    self.assertEqual(response, expected)
    search_documentation.assert_called_once_with(
        "device offline",
        limit=7,
        model="configured-embedding",
    )

def test_answer_request_uses_configured_answer_model(self) -> None:
    expected = {
        "query": "device offline",
        "answer": "Restart the agent [source-1].",
        "citations": ["source-1"],
        "sources": [],
    }

    with patch.dict(
        os.environ,
        {
            "AI_DOCS_DEFAULT_RETRIEVAL_LIMIT": "4",
            "AI_DOCS_EMBEDDING_MODEL": "configured-embedding",
            "AI_DOCS_ANSWER_MODEL": "configured-answer",
        },
        clear=True,
    ):
        with patch(
            "ai_docs.http_api.answer_question",
            return_value=expected,
        ) as answer_question:
            response = handle_answer_request(
                {"query": "device offline"}
            )

    self.assertEqual(response, expected)
    answer_question.assert_called_once_with(
        "device offline",
        limit=4,
        model="configured-embedding",
        answer_model="configured-answer",
    )

def test_diagnostics_response_hides_secrets(self) -> None:
    response = diagnostics_response()

    self.assertEqual(response["service"], "smarttouch-ai-docs")
    self.assertIn("database_configured", response)
    self.assertIn("openai_key_configured", response)
    self.assertIn("embedding_model", response)
    self.assertIn("answer_model", response)
    self.assertNotIn("database_url", response)
    self.assertNotIn("openai_api_key", response)

if __name__ == "__main__":
    unittest.main()
