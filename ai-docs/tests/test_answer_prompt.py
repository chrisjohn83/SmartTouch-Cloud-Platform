from __future__ import annotations

import unittest

from ai_docs.answer_prompt import build_answer_prompt


class AnswerPromptTests(unittest.TestCase):
    def test_builds_grounded_prompt_with_sources(self) -> None:
        answer_context = {
            "query": "A remote diagnostics session is already open",
            "contexts": [
                {
                    "citation_id": "source-1",
                    "title": "Common errors",
                    "heading_label": (
                        "Common errors > 'stctl' errors > "
                        "Error: session already open for protocol diagnostics"
                    ),
                    "source_url": "https://docs.example.com/common-errors/",
                    "excerpt": (
                        "List and close the existing session with "
                        "`stctl remote-access close <session_id>`."
                    ),
                }
            ],
        }

        prompt = build_answer_prompt(answer_context)

        self.assertIn("Use only the provided sources", prompt["system"])
        self.assertIn(
            "A remote diagnostics session is already open",
            prompt["user"],
        )
        self.assertIn("[source-1]", prompt["user"])
        self.assertIn("Common errors", prompt["user"])
        self.assertIn("stctl remote-access close", prompt["user"])
        self.assertIn(
            "Answer the question using only the sources above",
            prompt["user"],
        )

    def test_handles_empty_context(self) -> None:
        prompt = build_answer_prompt(
            {
                "query": "unknown thing",
                "contexts": [],
            }
        )

        self.assertIn("No sources were retrieved.", prompt["user"])
        self.assertIn(
            "does not provide enough information",
            prompt["system"],
        )


if __name__ == "__main__":
    unittest.main()
