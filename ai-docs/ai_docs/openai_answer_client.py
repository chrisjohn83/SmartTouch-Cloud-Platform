"""OpenAI-backed answer model client."""

from __future__ import annotations

from typing import Any

from openai import OpenAI


class OpenAIAnswerClient:
    """Generate grounded answers using OpenAI."""

    def __init__(
        self,
        *,
        model: str = "gpt-5.4-mini",
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.client = client or OpenAI()

    def generate(self, *, system: str, user: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": user,
                },
            ],
        )

        output_text = getattr(response, "output_text", None)

        if not output_text:
            raise ValueError("OpenAI response did not include output text")

        return output_text
