"""Command-line entry point for SmartTouch documentation ingestion."""

from __future__ import annotations

import argparse
import json
import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable

from .chunker import ChunkingConfig, chunk_document
from .models import DocumentChunk
from .parser import parse_markdown


def discover_markdown(docs_root: Path, exclude: Iterable[str] = ()) -> list[Path]:
    """Return deterministic Markdown inputs, honoring relative glob exclusions."""

    patterns = tuple(exclude)
    return [
        path
        for path in sorted(docs_root.rglob("*.md"))
        if not any(fnmatch(path.relative_to(docs_root).as_posix(), pattern) for pattern in patterns)
    ]


def ingest_documents(
    docs_root: Path,
    config: ChunkingConfig,
    exclude: Iterable[str] = (),
) -> list[DocumentChunk]:
    """Parse and chunk every Markdown file under a documentation root."""

    chunks: list[DocumentChunk] = []
    for path in discover_markdown(docs_root, exclude):
        document = parse_markdown(path, docs_root)
        chunks.extend(chunk_document(document, config))
    return chunks


def write_jsonl(chunks: Iterable[DocumentChunk], output: Path) -> int:
    """Write chunks atomically enough for local ingestion workflows."""

    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        for chunk in chunks:
            stream.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")
            count += 1
    return count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse SmartTouch MkDocs Markdown into retrieval-ready JSONL chunks."
    )
    parser.add_argument("--docs-root", type=Path, default=Path("docs"))
    parser.add_argument("--output", type=Path, default=Path("build/ai-docs/chunks.jsonl"))
    parser.add_argument("--site-url", default="https://chrisjohn83.github.io/SmartTouch-Cloud-Platform")
    parser.add_argument("--max-words", type=int, default=500)
    parser.add_argument("--overlap-words", type=int, default=60)
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="Exclude a docs-root-relative glob; may be passed more than once.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    docs_root = args.docs_root.resolve()
    if not docs_root.is_dir():
        print(f"error: documentation root does not exist: {docs_root}", file=sys.stderr)
        return 2

    config = ChunkingConfig(
        max_words=args.max_words,
        overlap_words=args.overlap_words,
        site_url=args.site_url,
    )
    chunks = ingest_documents(docs_root, config, args.exclude)
    count = write_jsonl(chunks, args.output)
    document_count = len({chunk.source_path for chunk in chunks})
    print(f"Wrote {count} chunks from {document_count} documents to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
