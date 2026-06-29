from __future__ import annotations

import unittest

from ai_docs.answer_generator import generate_answer


class FakeAnswerClient:
    def __init__(self, *answers: str) -> None:
        self.answers = list(answers)
        self.calls: list[dict[str, str]] = []

    def generate(self, *, system: str, user: str) -> str:
        self.calls.append(
            {
                "system": system,
                "user": user,
            }
        )

        if not self.answers:
            raise AssertionError("FakeAnswerClient has no answers left")

        if len(self.answers) == 1:
            return self.answers[0]

        return self.answers.pop(0)

class AnswerGeneratorTests(unittest.TestCase):
    def test_generates_answer_with_citations_and_sources(self) -> None:
        client = FakeAnswerClient(
            "Close the existing diagnostics session with "
            "`stctl remote-access close <session_id>` [source-1]."
        )
        answer_context = {
            "query": "A remote diagnostics session is already open",
            "contexts": [
                {
                    "citation_id": "source-1",
                    "title": "Common errors",
                    "heading": "Error: session already open",
                    "heading_label": (
                        "Common errors > Error: session already open"
                    ),
                    "source_path": "developers/onboarding/common-errors.md",
                    "source_url": "https://docs.example.com/common-errors/",
                    "excerpt": "Close the existing session.",
                }
            ],
        }

        response = generate_answer(
            answer_context,
            model_client=client,
        )

        self.assertEqual(
            response["query"],
            "A remote diagnostics session is already open",
        )
        self.assertIn("stctl remote-access close", response["answer"])
        self.assertEqual(response["citations"], ["source-1"])
        self.assertEqual(len(response["sources"]), 1)
        self.assertEqual(
            response["sources"][0]["source_url"],
            "https://docs.example.com/common-errors/",
        )
        self.assertEqual(len(client.calls), 1)
        self.assertIn(
            "Use only facts that appear in the provided sources",
            client.calls[0]["system"],
        )
        self.assertIn("[source-1]", client.calls[0]["user"])

    def test_retries_when_first_answer_is_uncited(self) -> None:
        answer_context = {
            "query": "A remote diagnostics session is already open",
            "contexts": [
                {
                    "citation_id": "source-1",
                    "title": "Common errors",
                    "heading": "Error: session already open for protocol diagnostics",
                    "heading_label": (
                        "Common errors > 'stctl' errors > "
                        "Error: session already open for protocol diagnostics"
                    ),
                    "source_url": "https://docs.example.com/common-errors/",
                    "source_path": "developers/onboarding/common-errors.md",
                    "excerpt": (
                        "Equivalent to HTTP 409 Conflict. List and close "
                        "the existing session:\n\n"
                        "```bash\n"
                        "stctl remote-access list --device <device_id> --status open\n"
                        "stctl remote-access close <session_id>\n"
                        "```"
                    ),
                }
            ],
        }

        fake_client = FakeAnswerClient(
            "List the existing open diagnostics session and close it.",
            (
                "List the existing open diagnostics session and close it. [source-1]\n\n"
                "```bash\n"
                "stctl remote-access list --device <device_id> --status open\n"
                "stctl remote-access close <session_id>\n"
                "``` [source-1]"
            ),
        )

        response = generate_answer(answer_context, model_client=fake_client)

        self.assertEqual(len(fake_client.calls), 2)
        self.assertEqual(response["citations"], ["source-1"])
        self.assertIn("[source-1]", response["answer"])

    def test_deduplicates_citations(self) -> None:
        client = FakeAnswerClient(
            "Use the documented command [source-1]. Then retry [source-1]."
        )
        answer_context = {
            "query": "What should I do?",
            "contexts": [
                {
                    "citation_id": "source-1",
                    "title": "Common errors",
                }
            ],
        }

        response = generate_answer(answer_context, model_client=client)

        self.assertEqual(response["citations"], ["source-1"])

    def test_ignores_unknown_citations(self) -> None:
        client = FakeAnswerClient(
            "Use the documented command [source-99]."
        )
        answer_context = {
            "query": "What should I do?",
            "contexts": [
                {
                    "citation_id": "source-1",
                    "title": "Common errors",
                }
            ],
        }

        response = generate_answer(answer_context, model_client=client)

        self.assertEqual(
            response["answer"],
            "The SmartTouch documentation does not provide enough cited "
            "information to answer this question.",
        )
        self.assertEqual(response["citations"], [])
        self.assertEqual(response["sources"], [])

    def test_rejects_answer_with_only_unknown_citations(self) -> None:
        client = FakeAnswerClient(
            "Use the documented command [source-99]."
        )
        answer_context = {
            "query": "What should I do?",
            "contexts": [
                {
                    "citation_id": "source-1",
                    "title": "Common errors",
                }
            ],
        }

        response = generate_answer(answer_context, model_client=client)

        self.assertEqual(
            response["answer"],
            "The SmartTouch documentation does not provide enough cited "
            "information to answer this question.",
        )
        self.assertEqual(response["citations"], [])
        self.assertEqual(response["sources"], [])

    def test_rejects_followup_offer(self) -> None:
        client = FakeAnswerClient(
            "Close the existing session. [source-1]\n\n"
            "If you want, I can help identify the session ID."
        )
        answer_context = {
            "query": "What should I do?",
            "contexts": [
                {
                    "citation_id": "source-1",
                    "title": "Common errors",
                    "heading": "Error: session already open",
                }
            ],
        }

        response = generate_answer(answer_context, model_client=client)

        self.assertEqual(
            response["answer"],
            "The SmartTouch documentation does not provide enough cited "
            "information to answer this question.",
        )
        self.assertEqual(response["citations"], [])
        self.assertEqual(response["sources"], [])

    def test_rejects_uncited_answer(self) -> None:
        client = FakeAnswerClient(
            "Restart the SmartTouch agent."
        )
        answer_context = {
            "query": "What should I do?",
            "contexts": [
                {
                    "citation_id": "source-1",
                    "title": "Common errors",
                }
            ],
        }

        response = generate_answer(answer_context, model_client=client)

        self.assertEqual(
            response["answer"],
            "The SmartTouch documentation does not provide enough cited "
            "information to answer this question.",
        )
        self.assertEqual(response["citations"], [])
        self.assertEqual(response["sources"], [])

    def test_returns_safe_answer_without_context(self) -> None:
        client = FakeAnswerClient("This should not be called.")
        answer_context = {
            "query": "Unknown question",
            "contexts": [],
        }

        response = generate_answer(answer_context, model_client=client)

        self.assertEqual(
            response["answer"],
            "The SmartTouch documentation does not provide enough cited "
            "information to answer this question.",
        )
        self.assertEqual(response["citations"], [])
        self.assertEqual(response["sources"], [])
        self.assertEqual(client.calls, [])

def test_retries_when_first_answer_is_uncited(self) -> None:
    client = FakeAnswerClient(
        "List the existing open diagnostics session and close it.",
        (
            "List the existing open diagnostics session and close it. [source-1]\n\n"
            "```bash\n"
            "stctl remote-access list --device <device_id> --status open\n"
            "stctl remote-access close <session_id>\n"
            "``` [source-1]"
        ),
    )

    response = generate_answer(
        self.answer_context,
        model_client=client,
    )

    self.assertEqual(len(client.calls), 2)
    self.assertEqual(response["citations"], ["source-1"])
    self.assertIn("[source-1]", response["answer"])

if __name__ == "__main__":
    unittest.main()
