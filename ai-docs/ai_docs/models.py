"""Data models shared by the ingestion pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class MarkdownSection:
    """A heading-delimited section from one Markdown document."""

    heading: str
    heading_path: tuple[str, ...]
    level: int
    content: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class MarkdownDocument:
    """A parsed Markdown source document."""

    source_path: str
    title: str
    metadata: dict[str, Any]
    sections: tuple[MarkdownSection, ...]
    content_hash: str


@dataclass(frozen=True)
class DocumentChunk:
    """A retrieval-ready unit emitted by the ingestion pipeline."""

    id: str
    source_path: str
    source_url: str | None
    title: str
    heading: str
    heading_path: tuple[str, ...]
    content: str
    content_hash: str
    chunk_index: int
    start_line: int
    end_line: int
    word_count: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        record = asdict(self)
        record["heading_path"] = list(self.heading_path)
        return record
