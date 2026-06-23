"""Convert parsed Markdown sections into retrieval-sized chunks."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from urllib.parse import quote

from .models import DocumentChunk, MarkdownDocument, MarkdownSection


@dataclass(frozen=True)
class ChunkingConfig:
    """Tuning values for section-aware chunking."""

    max_words: int = 500
    overlap_words: int = 60
    site_url: str | None = None

    def __post_init__(self) -> None:
        if self.max_words < 50:
            raise ValueError("max_words must be at least 50")
        if self.overlap_words < 0:
            raise ValueError("overlap_words cannot be negative")
        if self.overlap_words >= self.max_words:
            raise ValueError("overlap_words must be smaller than max_words")


def _word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _markdown_blocks(text: str) -> list[str]:
    """Split on blank lines while keeping fenced code blocks intact."""

    blocks: list[str] = []
    current: list[str] = []
    fence_marker: str | None = None

    for line in text.splitlines():
        stripped = line.lstrip()
        fence_match = re.match(r"(`{3,}|~{3,})", stripped)
        if fence_match:
            marker = fence_match.group(1)
            if fence_marker is None:
                fence_marker = marker[0]
            elif marker[0] == fence_marker:
                fence_marker = None

        if not line.strip() and fence_marker is None:
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        current.append(line)

    if current:
        blocks.append("\n".join(current).strip())
    return [block for block in blocks if block]


def _tail_words(blocks: list[str], target_words: int) -> list[str]:
    if target_words == 0:
        return []

    selected: list[str] = []
    count = 0
    for block in reversed(blocks):
        selected.insert(0, block)
        count += _word_count(block)
        if count >= target_words:
            break
    return selected


def _split_section(section: MarkdownSection, config: ChunkingConfig) -> list[str]:
    if _word_count(section.content) <= config.max_words:
        return [section.content]

    blocks = _markdown_blocks(section.content)
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    for block in blocks:
        block_words = _word_count(block)
        if current and current_words + block_words > config.max_words:
            chunks.append("\n\n".join(current))
            current = _tail_words(current, config.overlap_words)
            current_words = sum(_word_count(item) for item in current)

        # A fenced code block or table should remain intact even if it exceeds the target.
        if current and current_words + block_words > config.max_words:
            current = []
            current_words = 0

        current.append(block)
        current_words += block_words

    if current:
        candidate = "\n\n".join(current)
        if not chunks or candidate != chunks[-1]:
            chunks.append(candidate)

    return chunks


def _has_section_body(section: MarkdownSection) -> bool:
    lines = section.content.splitlines()
    return section.level == 0 or any(line.strip() for line in lines[1:])


def _source_url(site_url: str | None, source_path: str) -> str | None:
    if not site_url:
        return None
    route = source_path[:-3] if source_path.endswith(".md") else source_path
    if route.endswith("/index"):
        route = route[: -len("index")]
    return f"{site_url.rstrip('/')}/{quote(route, safe='/')}/".replace("//", "//", 1)


def chunk_document(
    document: MarkdownDocument,
    config: ChunkingConfig | None = None,
) -> list[DocumentChunk]:
    """Create deterministic retrieval records for one parsed document."""

    config = config or ChunkingConfig()
    chunks: list[DocumentChunk] = []
    source_url = _source_url(config.site_url, document.source_path)

    for section in document.sections:
        if not _has_section_body(section):
            continue
        for part in _split_section(section, config):
            chunk_index = len(chunks)
            identity = f"{document.source_path}\0{section.heading_path}\0{part}"
            chunk_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
            content_hash = hashlib.sha256(part.encode("utf-8")).hexdigest()

            metadata = {
                **document.metadata,
                "document_content_hash": document.content_hash,
                "section_level": section.level,
            }

            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    source_path=document.source_path,
                    source_url=source_url,
                    title=document.title,
                    heading=section.heading,
                    heading_path=section.heading_path,
                    content=part,
                    content_hash=content_hash,
                    chunk_index=chunk_index,
                    start_line=section.start_line,
                    end_line=section.end_line,
                    word_count=_word_count(part),
                    metadata=metadata,
                )
            )

    return chunks
