"""Provider-independent embedding contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class EmbeddingResult:
    vector: list[float]
    model: str
    dimensions: int


class EmbeddingProvider(ABC):
    """Interface implemented by hosted or local embedding providers."""

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[EmbeddingResult]:
        """Generate one embedding result for every supplied text."""
    