from __future__ import annotations

import unittest

from ai_docs.retrieval_api import build_search_response


class RetrievalApiTests(unittest.TestCase):
    def test_builds_stable_search_response(self) -> None:
        results = [
            {
                "id": "chunk-1",
                "title": "Common errors",
                "heading": "Error: session already open",
                "heading_path": [
                    "Common errors",
                    "'stctl' errors",
                    "Error: session already open",
                ],
                "source_path": "developers/onboarding/common-errors.md",
                "source_url": "https://docs.example.com/common-errors/",
                "content": "Close the existing diagnostics session.",
                "metadata": {"persona": ["developer"]},
                "final_score": 0.015,
                "semantic_score": 0.552,
                "lexical_score": 1.05,
                "semantic_rank": 14,
                "lexical_rank": 1,
            }
        ]
        original = [record.copy() for record in results]

        response = build_search_response(
            "A remote diagnostics session is already open",
            results,
        )

        self.assertEqual(
            response["query"],
            "A remote diagnostics session is already open",
        )
        self.assertEqual(response["result_count"], 1)
        self.assertEqual(len(response["results"]), 1)

        result = response["results"][0]
        self.assertEqual(result["id"], "chunk-1")
        self.assertEqual(
            result["heading_path"],
            [
                "Common errors",
                "'stctl' errors",
                "Error: session already open",
            ],
        )
        self.assertEqual(result["scores"]["final"], 0.015)
        self.assertEqual(result["scores"]["semantic"], 0.552)
        self.assertEqual(result["scores"]["lexical"], 1.05)
        self.assertEqual(result["ranks"]["semantic"], 14)
        self.assertEqual(result["ranks"]["lexical"], 1)
        self.assertEqual(result["metadata"], {"persona": ["developer"]})

        self.assertEqual(results, original)

    def test_supports_semantic_only_scores(self) -> None:
        response = build_search_response(
            "Kubernetes cannot pull my image",
            [
                {
                    "id": "chunk-2",
                    "heading_path": ["Deployment", "ImagePullBackOff"],
                    "score": 0.72,
                }
            ],
        )

        result = response["results"][0]

        self.assertEqual(result["scores"]["final"], 0.72)
        self.assertIsNone(result["scores"]["semantic"])
        self.assertIsNone(result["scores"]["lexical"])
        self.assertIsNone(result["ranks"]["semantic"])
        self.assertIsNone(result["ranks"]["lexical"])


if __name__ == "__main__":
    unittest.main()
