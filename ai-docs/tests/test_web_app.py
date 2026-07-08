from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from ai_docs.retrieval_service import RetrievalServiceError
from ai_docs.web_app import app


class WebAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_endpoint(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "service": "smarttouch-ai-docs",
            },
        )

    def test_diagnostics_endpoint(self) -> None:
        response = self.client.get("/diagnostics")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["service"], "smarttouch-ai-docs")
        self.assertIn("database_configured", body)
        self.assertIn("openai_key_configured", body)
        self.assertNotIn("database_url", body)
        self.assertNotIn("openai_api_key", body)
        self.assertIn("knowledge_graph_configured", body)
        self.assertIn("knowledge_graph_entities_path", body)
        self.assertIn("knowledge_graph_relationships_path", body)

    def test_cors_allows_github_pages_origin(self) -> None:
        response = self.client.options(
            "/answer",
            headers={
                "Origin": "https://chrisjohn83.github.io",
                "Access-Control-Request-Method": "POST",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "https://chrisjohn83.github.io",
        )

    def test_search_endpoint(self) -> None:
        expected = {
            "query": "device offline",
            "result_count": 0,
            "results": [],
        }

        with patch(
            "ai_docs.web_app.handle_search_request",
            return_value=expected,
        ) as handle_search_request:
            response = self.client.post(
                "/search",
                json={
                    "query": "device offline",
                    "limit": 3,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        handle_search_request.assert_called_once_with(
            {
                "query": "device offline",
                "limit": 3,
            }
        )

    def test_answer_context_endpoint(self) -> None:
        expected = {
            "query": "device offline",
            "context_count": 0,
            "contexts": [],
        }

        with patch(
            "ai_docs.web_app.handle_answer_context_request",
            return_value=expected,
        ) as handle_answer_context_request:
            response = self.client.post(
                "/answer-context",
                json={
                    "query": "device offline",
                    "limit": 3,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        handle_answer_context_request.assert_called_once_with(
            {
                "query": "device offline",
                "limit": 3,
            }
        )

    def test_validation_errors_return_400(self) -> None:
        response = self.client.post(
            "/search",
            json={
                "query": "",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "query is required")

    def test_dependency_errors_return_503(self) -> None:
        with patch(
            "ai_docs.web_app.handle_search_request",
            side_effect=RetrievalServiceError(
                "Retrieval service is unavailable"
            ),
        ):
            response = self.client.post(
                "/search",
                json={"query": "device offline"},
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"],
            "Retrieval service is unavailable",
        )

    def test_answer_endpoint(self) -> None:
        expected = {
            "query": "device offline",
            "answer": "Restart the agent [source-1].",
            "citations": ["source-1"],
            "sources": [],
        }

        with patch(
            "ai_docs.web_app.handle_answer_request",
            return_value=expected,
        ) as handle_answer_request:
            response = self.client.post(
                "/answer",
                json={
                    "query": "device offline",
                    "limit": 3,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        handle_answer_request.assert_called_once_with(
            {
                "query": "device offline",
                "limit": 3,
            }
        )

if __name__ == "__main__":
    unittest.main()
