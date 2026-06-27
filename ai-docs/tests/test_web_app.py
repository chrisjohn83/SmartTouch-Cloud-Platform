from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

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


if __name__ == "__main__":
    unittest.main()
