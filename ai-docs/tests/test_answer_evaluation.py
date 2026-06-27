from __future__ import annotations

import unittest

from ai_docs.answer_generator import INSUFFICIENT_CITED_INFORMATION
from ai_docs.evaluate_answers import evaluate_answer_response


class AnswerEvaluationTests(unittest.TestCase):
    def test_accepts_valid_answer(self) -> None:
        case = {
            "required_citations": ["source-1"],
            "required_answer_contains": ["stctl remote-access close"],
            "forbidden_answer_contains": ["if you want"],
            "allow_fallback": False,
        }
        response = {
            "answer": (
                "Close the session. [source-1]\n\n"
                "```bash\n"
                "stctl remote-access close <session_id>\n"
                "```"
            ),
            "citations": ["source-1"],
        }

        self.assertEqual(evaluate_answer_response(case, response), [])

    def test_rejects_missing_required_citation(self) -> None:
        case = {
            "required_citations": ["source-1"],
        }
        response = {
            "answer": "Close the session.",
            "citations": [],
        }

        self.assertIn(
            "missing required citation: source-1",
            evaluate_answer_response(case, response),
        )

    def test_rejects_forbidden_text(self) -> None:
        case = {
            "forbidden_answer_contains": ["if you want"],
        }
        response = {
            "answer": "If you want, I can help.",
            "citations": [],
        }

        self.assertIn(
            "answer contains forbidden text: if you want",
            evaluate_answer_response(case, response),
        )

    def test_rejects_unexpected_fallback(self) -> None:
        case = {
            "allow_fallback": False,
        }
        response = {
            "answer": INSUFFICIENT_CITED_INFORMATION,
            "citations": [],
        }

        self.assertIn(
            "answer unexpectedly returned fallback",
            evaluate_answer_response(case, response),
        )


if __name__ == "__main__":
    unittest.main()
