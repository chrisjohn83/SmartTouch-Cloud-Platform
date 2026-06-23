"""OpenAI implementation of the embedding provider."""

from __future__ import annotations

from typing import Any, Sequence

from openai import OpenAI

from .embeddings import EmbeddingProvider, EmbeddingResult


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Generate embeddings through the OpenAI API."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        dimensions: int | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.dimensions = dimensions
        self.client = client or OpenAI()

    def embed(self, texts: Sequence[str]) -> list[EmbeddingResult]:
        clean_texts = [text.strip() for text in texts]

        if not clean_texts:
            return []

        if any(not text for text in clean_texts):
            raise ValueError("Embedding input cannot be empty")

        request: dict[str, Any] = {
            "model": self.model,
            "input": clean_texts,
            "encoding_format": "float",
        }

        if self.dimensions is not None:
            request["dimensions"] = self.dimensions

        response = self.client.embeddings.create(**request)

        ordered_data = sorted(
            response.data,
            key=lambda item: item.index,
        )

        if len(ordered_data) != len(clean_texts):
            raise RuntimeError(
                "OpenAI returned a different number of embeddings "
                "than the number of input texts"
            )

        return [
            EmbeddingResult(
                vector=list(item.embedding),
                model=response.model,
                dimensions=len(item.embedding),
            )
            for item in ordered_data
        ]
