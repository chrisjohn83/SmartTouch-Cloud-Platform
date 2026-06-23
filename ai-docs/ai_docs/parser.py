"""Parse MkDocs Markdown into front matter and heading-delimited sections."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

from .models import MarkdownDocument, MarkdownSection

HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")


def _json_safe(value: Any) -> Any:
    """Normalize YAML values such as dates into JSON-safe values."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _split_front_matter(text: str) -> tuple[dict[str, Any], str, int]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text, 1

    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if closing_index is None:
        raise ValueError("Markdown front matter starts with '---' but has no closing delimiter")

    raw_metadata = "".join(lines[1:closing_index])
    loaded = yaml.safe_load(raw_metadata) or {}
    if not isinstance(loaded, dict):
        raise ValueError("Markdown front matter must be a YAML mapping")

    body = "".join(lines[closing_index + 1 :])
    return _json_safe(loaded), body, closing_index + 2


def _clean_heading(raw_heading: str) -> str:
    """Remove common inline formatting without flattening meaningful text."""

    heading = re.sub(r"\s+\{#[^}]+\}\s*$", "", raw_heading)
    heading = re.sub(r"[`*_]", "", heading)
    return heading.strip()


def _find_headings(lines: list[str]) -> list[tuple[int, int, str]]:
    headings: list[tuple[int, int, str]] = []
    fence_marker: str | None = None

    for index, line in enumerate(lines):
        stripped = line.lstrip()
        fence_match = re.match(r"(`{3,}|~{3,})", stripped)
        if fence_match:
            marker = fence_match.group(1)
            if fence_marker is None:
                fence_marker = marker[0]
            elif marker[0] == fence_marker:
                fence_marker = None
            continue

        if fence_marker is not None:
            continue

        match = HEADING_RE.match(line.rstrip("\r\n"))
        if match:
            headings.append((index, len(match.group(1)), _clean_heading(match.group(2))))

    return headings


def _build_sections(body: str, body_start_line: int) -> tuple[MarkdownSection, ...]:
    lines = body.splitlines()
    headings = _find_headings(lines)
    sections: list[MarkdownSection] = []
    heading_stack: list[tuple[int, str]] = []

    if headings and headings[0][0] > 0:
        preamble = "\n".join(lines[: headings[0][0]]).strip()
        if preamble:
            sections.append(
                MarkdownSection(
                    heading="Introduction",
                    heading_path=("Introduction",),
                    level=0,
                    content=preamble,
                    start_line=body_start_line,
                    end_line=body_start_line + headings[0][0] - 1,
                )
            )

    if not headings:
        content = body.strip()
        if not content:
            return ()
        return (
            MarkdownSection(
                heading="Document",
                heading_path=("Document",),
                level=0,
                content=content,
                start_line=body_start_line,
                end_line=body_start_line + max(len(lines) - 1, 0),
            ),
        )

    for position, (line_index, level, heading) in enumerate(headings):
        next_index = headings[position + 1][0] if position + 1 < len(headings) else len(lines)

        while heading_stack and heading_stack[-1][0] >= level:
            heading_stack.pop()
        heading_stack.append((level, heading))

        section_body = "\n".join(lines[line_index + 1 : next_index]).strip()
        content = f"{'#' * level} {heading}"
        if section_body:
            content = f"{content}\n\n{section_body}"

        sections.append(
            MarkdownSection(
                heading=heading,
                heading_path=tuple(item[1] for item in heading_stack),
                level=level,
                content=content,
                start_line=body_start_line + line_index,
                end_line=body_start_line + max(next_index - 1, line_index),
            )
        )

    return tuple(sections)


def parse_markdown(path: Path, docs_root: Path) -> MarkdownDocument:
    """Parse one UTF-8 Markdown file relative to a documentation root."""

    text = path.read_text(encoding="utf-8-sig")
    metadata, body, body_start_line = _split_front_matter(text)
    sections = _build_sections(body, body_start_line)
    title_section = next((section for section in sections if section.level == 1), None)
    title = str(metadata.get("title") or (title_section.heading if title_section else path.stem))
    source_path = path.relative_to(docs_root).as_posix()

    return MarkdownDocument(
        source_path=source_path,
        title=title,
        metadata=metadata,
        sections=sections,
        content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )
