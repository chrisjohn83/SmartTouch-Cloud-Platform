from __future__ import annotations

import unittest

from ai_docs.answer_context import build_answer_context


class AnswerContextTests(unittest.TestCase):
    def test_builds_citation_ready_context(self) -> None:
        search_response = {
            "query": "A remote diagnostics session is already open",
            "result_count": 1,
            "results": [
                {
                    "title": "Common errors",
                    "heading": "Error: session already open for protocol diagnostics",
                    "heading_path": [
                        "Common errors",
                        "'stctl' errors",
                        "Error: session already open for protocol diagnostics",
                    ],
                    "source_path": "developers/onboarding/common-errors.md",
                    "source_url": "https://docs.example.com/common-errors/",
                    "content": "List and close the existing session.",
                    "scores": {
                        "final": 0.023,
                        "semantic": 0.552,
                        "lexical": 0.0125,
                    },
                    "ranks": {
                        "semantic": 14,
                        "lexical": 1,
                    },
                }
            ],
        }

        context = build_answer_context(search_response)

        self.assertEqual(
            context["query"],
            "A remote diagnostics session is already open",
        )
        self.assertEqual(context["context_count"], 1)

        item = context["contexts"][0]
        self.assertEqual(item["citation_id"], "source-1")
        self.assertEqual(item["title"], "Common errors")
        self.assertEqual(
            item["heading_label"],
            "Common errors > 'stctl' errors > "
            "Error: session already open for protocol diagnostics",
        )
        self.assertEqual(
            item["source_url"],
            "https://docs.example.com/common-errors/",
        )
        self.assertEqual(
            item["excerpt"],
            "List and close the existing session.",
        )
        self.assertEqual(item["scores"]["final"], 0.023)
        self.assertEqual(item["ranks"]["lexical"], 1)

    def test_limits_results_and_truncates_content(self) -> None:
        search_response = {
            "query": "device offline",
            "results": [
                {
                    "heading_path": ["One"],
                    "content": "abcdef",
                },
                {
                    "heading_path": ["Two"],
                    "content": "ghijkl",
                },
            ],
        }

        context = build_answer_context(
            search_response,
            max_results=1,
            max_content_chars=4,
        )

        self.assertEqual(context["context_count"], 1)
        self.assertEqual(context["contexts"][0]["citation_id"], "source-1")
        self.assertEqual(context["contexts"][0]["excerpt"], "abc…")

    def test_rejects_invalid_limits(self) -> None:
        with self.assertRaisesRegex(ValueError, "max_results"):
            build_answer_context({"results": []}, max_results=0)

        with self.assertRaisesRegex(ValueError, "max_content_chars"):
            build_answer_context({"results": []}, max_content_chars=0)


if __name__ == "__main__":
    unittest.main()
