from __future__ import annotations

import unittest
from dataclasses import dataclass

from ai_docs.openai_answer_client import OpenAIAnswerClient


@dataclass
class FakeResponse:
    output_text: str | None


class FakeResponses:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls = []

    def create(self, **request):
        self.calls.append(request)
        return self.response


class FakeOpenAIClient:
    def __init__(self, response: FakeResponse) -> None:
        self.responses = FakeResponses(response)


class OpenAIAnswerClientTests(unittest.TestCase):
    def test_generates_answer_using_responses_api(self) -> None:
        fake_openai = FakeOpenAIClient(
            FakeResponse("Close the session [source-1].")
        )
        client = OpenAIAnswerClient(
            model="gpt-5.4-mini",
            client=fake_openai,
        )

        answer = client.generate(
            system="Use only sources.",
            user="Question and sources.",
        )

        self.assertEqual(answer, "Close the session [source-1].")
        self.assertEqual(len(fake_openai.responses.calls), 1)

        request = fake_openai.responses.calls[0]
        self.assertEqual(request["model"], "gpt-5.4-mini")
        self.assertEqual(
            request["input"],
            [
                {
                    "role": "system",
                    "content": "Use only sources.",
                },
                {
                    "role": "user",
                    "content": "Question and sources.",
                },
            ],
        )

    def test_rejects_missing_output_text(self) -> None:
        fake_openai = FakeOpenAIClient(FakeResponse(None))
        client = OpenAIAnswerClient(client=fake_openai)

        with self.assertRaisesRegex(
            ValueError,
            "did not include output text",
        ):
            client.generate(
                system="Use only sources.",
                user="Question and sources.",
            )


if __name__ == "__main__":
    unittest.main()
