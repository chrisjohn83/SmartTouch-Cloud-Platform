from __future__ import annotations

import json
import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace

from ai_docs.chunker import ChunkingConfig, chunk_document
from ai_docs.embedding_filter import searchable_text, should_embed
from ai_docs.embedding_index import index_embeddings, load_completed_ids
from ai_docs.embeddings import EmbeddingProvider, EmbeddingResult
from ai_docs.embedding_input import build_embedding_input
from ai_docs.evaluate_retrieval import QueryEmbeddingCache
from ai_docs.ingest import discover_markdown, write_jsonl
from ai_docs.openai_embeddings import OpenAIEmbeddingProvider
from ai_docs.parser import parse_markdown
from ai_docs.semantic_search import (
    cosine_similarity,
    lexical_scores,
    longest_heading_phrase,
    normalize_text,
    rank_records,
    rank_records_hybrid,
    tokenize,
)

SAMPLE = """---
persona: [developer]
last-reviewed: "2026-06-08"
ai-retrieval-questions:
  - "Why is my device offline?"
---

# Device troubleshooting

An introduction to the guide.

## Quick diagnosis

Run the following command:

```bash
# This is not a Markdown heading.
stctl device status sensor-001
```

## Resolution

Restart the agent.
"""

FIXTURES = Path(__file__).parent / "fixtures"

class FakeEmbeddingsResource:
    def __init__(self) -> None:
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs

        return SimpleNamespace(
            model=kwargs["model"],
            data=[
                SimpleNamespace(
                    index=index,
                    embedding=[float(index), 0.5, 1.0],
                )
                for index, _ in enumerate(kwargs["input"])
            ],
        )

class FakeOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddingsResource()

class ParserTests(unittest.TestCase):
    def test_parses_front_matter_and_heading_hierarchy(self) -> None:
        document = parse_markdown(FIXTURES / "guide.md", FIXTURES)

        self.assertEqual(document.title, "Device troubleshooting")
        self.assertEqual(document.metadata["persona"], ["developer"])
        self.assertEqual(len(document.sections), 3)
        self.assertEqual(
            document.sections[1].heading_path,
            ("Device troubleshooting", "Quick diagnosis"),
        )
        self.assertIn("# This is not a Markdown heading.", document.sections[1].content)

    def test_chunk_ids_are_deterministic_and_metadata_is_preserved(self) -> None:
        document = parse_markdown(FIXTURES / "guide.md", FIXTURES)
        first = chunk_document(
            document,
            ChunkingConfig(site_url="https://docs.example.com"),
        )
        second = chunk_document(
            document,
            ChunkingConfig(site_url="https://docs.example.com"),
        )

        self.assertEqual([chunk.id for chunk in first], [chunk.id for chunk in second])
        self.assertEqual(first[0].metadata["persona"], ["developer"])
        self.assertEqual(first[0].source_url, "https://docs.example.com/guide/")

    def test_large_sections_split_without_breaking_code_fences(self) -> None:
        document = parse_markdown(FIXTURES / "large.md", FIXTURES)
        chunks = chunk_document(
            document,
            ChunkingConfig(max_words=100, overlap_words=20),
        )

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.content.strip() for chunk in chunks))

class OpenAIEmbeddingProviderTests(unittest.TestCase):
    def test_embeds_batch_using_openai_client(self) -> None:
        client = FakeOpenAIClient()
        provider = OpenAIEmbeddingProvider(
            model="text-embedding-3-small",
            client=client,
        )

        results = provider.embed([
            "Device troubleshooting",
            "Certificate validation",
        ])

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].model, "text-embedding-3-small")
        self.assertEqual(results[0].dimensions, 3)
        self.assertEqual(results[1].vector, [1.0, 0.5, 1.0])

        self.assertEqual(
            client.embeddings.last_request["input"],
            [
                "Device troubleshooting",
                "Certificate validation",
            ],
        )
        self.assertEqual(
            client.embeddings.last_request["encoding_format"],
            "float",
        )

    def test_rejects_empty_embedding_input(self) -> None:
        provider = OpenAIEmbeddingProvider(
            client=FakeOpenAIClient(),
        )

        with self.assertRaises(ValueError):
            provider.embed([""])

class CliHelpersTests(unittest.TestCase):
    def test_discovery_exclusions_and_jsonl_output(self) -> None:
        paths = discover_markdown(FIXTURES, ["drafts/**", "large.md"])
        document = parse_markdown(paths[0], FIXTURES)
        chunks = chunk_document(document)
        output = Path("build/test-chunks.jsonl")
        count = write_jsonl(chunks, output)
        records = [
            json.loads(line)
            for line in output.read_text(encoding="utf-8").splitlines()
        ]

        self.assertEqual([path.name for path in paths], ["guide.md"])
        self.assertEqual(count, 3)
        self.assertEqual(records[0]["source_path"], "guide.md")

class EmbeddingInputTests(unittest.TestCase):
    def test_builds_embedding_input_from_chunk(self) -> None:
        chunk = {
            "title": "Why is my device not connecting?",
            "heading_path": [
                "Why is my device not connecting?",
                "Quick diagnosis",
            ],
            "content": "Run stctl device agent-status sensor-001.",
            "metadata": {
                "task": ["remote-access", "troubleshooting"],
                "tags": ["device", "agent"],
                "ai-retrieval-questions": [
                    "Why is my device offline?",
                    "How do I diagnose the agent?",
                ],
            },
        }

        result = build_embedding_input(chunk)

        self.assertIn(
            "Document: Why is my device not connecting?",
            result,
        )
        self.assertIn(
            "Section: Why is my device not connecting? > Quick diagnosis",
            result,
        )
        self.assertIn(
            "Tasks: remote-access, troubleshooting",
            result,
        )
        self.assertIn(
            "Topics: device, agent",
            result,
        )
        self.assertIn(
            "- Why is my device offline?",
            result,
        )
        self.assertIn(
            "Content:\nRun stctl device agent-status sensor-001.",
            result,
        )

class EmbeddingIndexTests(unittest.TestCase):
    def test_indexes_chunks_and_resumes_without_duplicates(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            input_path = root / "chunks.jsonl"
            output_path = root / "embedded.jsonl"

            chunks = [
                {
                    "id": "chunk-1",
                    "title": "Device troubleshooting",
                    "heading_path": ["Quick diagnosis"],
                    "content": "Check the device agent status.",
                    "metadata": {},
                },
                {
                    "id": "chunk-2",
                    "title": "Certificate validation",
                    "heading_path": ["Certificate error"],
                    "content": "Inspect the certificate expiry date.",
                    "metadata": {},
                },
            ]

            input_path.write_text(
                "".join(
                    json.dumps(chunk) + "\n"
                    for chunk in chunks
                ),
                encoding="utf-8",
            )

            provider = FakeEmbeddingProvider()

            first_count, first_pending = index_embeddings(
                input_path,
                output_path,
                provider,
                batch_size=1,
            )

            second_count, second_pending = index_embeddings(
                input_path,
                output_path,
                provider,
                batch_size=1,
            )

            records = [
                json.loads(line)
                for line in output_path.read_text(
                    encoding="utf-8"
                ).splitlines()
            ]

        self.assertEqual(first_count, 2)
        self.assertEqual(first_pending, 2)
        self.assertEqual(second_count, 0)
        self.assertEqual(second_pending, 0)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["embedding"]["dimensions"], 3)
        self.assertEqual(
            {record["id"] for record in records},
            {"chunk-1", "chunk-2"},
        )
    def test_limits_number_of_embedded_chunks(self) -> None:
        root = Path("build/test-limit")
        root.mkdir(parents=True, exist_ok=True)

        input_path = root / "chunks.jsonl"
        output_path = root / "embedded.jsonl"

        if output_path.exists():
            output_path.unlink()

        chunks = [
            {
                "id": f"chunk-{index}",
                "title": f"Document {index}",
                "heading_path": ["Section"],
                "content": f"Searchable content {index}",
                "metadata": {},
            }
            for index in range(3)
        ]

        input_path.write_text(
            "".join(json.dumps(chunk) + "\n" for chunk in chunks),
            encoding="utf-8",
        )

        embedded, pending = index_embeddings(
            input_path,
            output_path,
            FakeEmbeddingProvider(),
            batch_size=2,
            limit=2,
        )

        records = [
            json.loads(line)
            for line in output_path.read_text(
                encoding="utf-8"
            ).splitlines()
        ]

        self.assertEqual(embedded, 2)
        self.assertEqual(pending, 2)
        self.assertEqual(len(records), 2)

    def test_loads_completed_chunk_ids(self) -> None:
        root = Path("build/test-completed")
        root.mkdir(parents=True, exist_ok=True)

        output = root / "embedded.jsonl"
        output.write_text(
            '{"id": "chunk-1"}\n{"id": "chunk-2"}\n',
            encoding="utf-8",
        )

        completed = load_completed_ids(output)
        self.assertEqual(completed, {"chunk-1", "chunk-2"})

class SemanticSearchTests(unittest.TestCase):
    def test_cosine_similarity(self) -> None:
        self.assertAlmostEqual(
            cosine_similarity([1.0, 0.0], [1.0, 0.0]),
            1.0,
        )
        self.assertAlmostEqual(
            cosine_similarity([1.0, 0.0], [0.0, 1.0]),
            0.0,
        )

    def test_ranks_most_similar_record_first(self) -> None:
        records = [
            {
                "id": "certificate",
                "embedding": {
                    "vector": [0.0, 1.0],
                },
            },
            {
                "id": "device-agent",
                "embedding": {
                    "vector": [1.0, 0.0],
                },
            },
        ]

        ranked = rank_records(
            query_vector=[0.9, 0.1],
            records=records,
            limit=2,
        )

        self.assertEqual(
            ranked[0][1]["id"],
            "device-agent",
        )
        self.assertGreater(
            ranked[0][0],
            ranked[1][0],
        )

    def test_normalizes_punctuation_commands_and_apostrophes(self) -> None:
        self.assertEqual(
            normalize_text("Why can’t `stctl remote-access` open?"),
            "why cant stctl remote-access open",
        )
        self.assertEqual(
            tokenize("Error: session_already-open."),
            ["error", "session_already-open"],
        )
        self.assertEqual(
            longest_heading_phrase(
                "A remote diagnostics session is already open",
                "Error: session already open for protocol diagnostics",
            ),
            3,
        )

    def test_lexical_score_favors_exact_error_heading(self) -> None:
        records = [
            {
                "title": "Remote access",
                "heading_path": [
                    "Common errors",
                    "Error: session already open for protocol diagnostics",
                ],
                "content": (
                    "A diagnostics session is already open. "
                    "List and close the existing session."
                ),
                "metadata": {},
            },
            {
                "title": "Remote access",
                "heading_path": ["Open a diagnostics session"],
                "content": "Open a new diagnostics session for the device.",
                "metadata": {},
            },
        ]

        scores = lexical_scores(
            "A remote diagnostics session is already open",
            records,
        )

        self.assertGreater(scores[0], scores[1])

    def test_hybrid_fusion_is_deterministic_and_does_not_mutate(self) -> None:
        records = [
            {
                "id": "semantic",
                "title": "Device troubleshooting",
                "heading_path": ["Agent offline"],
                "content": "Check why the device cannot connect.",
                "metadata": {},
                "embedding": {"vector": [1.0, 0.0]},
            },
            {
                "id": "lexical",
                "title": "Unrelated keyword list",
                "heading_path": ["Device connect troubleshooting"],
                "content": "device connect device connect device connect",
                "metadata": {},
                "embedding": {"vector": [0.7, 0.7]},
            },
        ]
        original = json.loads(json.dumps(records))

        first = rank_records_hybrid(
            "Why can my device not connect?",
            [1.0, 0.0],
            records,
            limit=2,
        )
        second = rank_records_hybrid(
            "Why can my device not connect?",
            [1.0, 0.0],
            records,
            limit=2,
        )

        self.assertEqual([item.record["id"] for item in first], ["semantic", "lexical"])
        self.assertEqual(
            [item.final_score for item in first],
            [item.final_score for item in second],
        )
        self.assertEqual(records, original)

    def test_hybrid_places_exact_error_within_top_three(self) -> None:
        records = [
            {
                "id": "generic-1",
                "title": "Remote access",
                "heading_path": ["Open a diagnostics session"],
                "content": "Start a new diagnostics connection.",
                "metadata": {},
                "embedding": {"vector": [1.0, 0.0]},
            },
            {
                "id": "generic-2",
                "title": "Remote access",
                "heading_path": ["Troubleshooting"],
                "content": "Troubleshoot the remote connection.",
                "metadata": {},
                "embedding": {"vector": [0.99, 0.01]},
            },
            {
                "id": "generic-3",
                "title": "Remote access",
                "heading_path": ["Session protocols"],
                "content": "Supported protocols include diagnostics.",
                "metadata": {},
                "embedding": {"vector": [0.98, 0.02]},
            },
            {
                "id": "exact-error",
                "title": "Common errors",
                "heading_path": [
                    "Error: session already open for protocol diagnostics"
                ],
                "content": "Close the existing session before retrying.",
                "metadata": {
                    "ai-retrieval-questions": [
                        "A remote diagnostics session is already open"
                    ]
                },
                "embedding": {"vector": [0.8, 0.2]},
            },
        ]

        ranked = rank_records_hybrid(
            "A remote diagnostics session is already open",
            [1.0, 0.0],
            records,
            limit=4,
        )
        ids = [result.record["id"] for result in ranked]

        self.assertLess(ids.index("exact-error"), 3)
        exact = next(
            result for result in ranked if result.record["id"] == "exact-error"
        )
        self.assertTrue(exact.lexical_promoted)

class FakeEmbeddingProvider(EmbeddingProvider):
    def embed(self, texts):
        return [
            EmbeddingResult(
                vector=[float(len(text)), 1.0, 0.5],
                model="fake-embedding-model",
                dimensions=3,
            )
            for text in texts
        ]

class EmbeddingProviderTests(unittest.TestCase):
    def test_provider_returns_one_result_per_text(self) -> None:
        provider = FakeEmbeddingProvider()

        results = provider.embed([
            "Device troubleshooting",
            "Certificate validation",
        ])

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].model, "fake-embedding-model")
        self.assertEqual(results[0].dimensions, 3)
        self.assertEqual(len(results[0].vector), 3)


class CountingEmbeddingProvider(FakeEmbeddingProvider):
    def __init__(self) -> None:
        self.calls = 0

    def embed(self, texts):
        self.calls += 1
        return super().embed(texts)


class QueryEmbeddingCacheTests(unittest.TestCase):
    def test_reuses_cached_query_embedding(self) -> None:
        cache_path = Path("build/test-query-cache.json")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        if cache_path.exists():
            cache_path.unlink()

        provider = CountingEmbeddingProvider()
        cache = QueryEmbeddingCache(cache_path)

        first = cache.get_or_create(
            "test-model",
            "Why can’t my device connect?",
            provider,
        )
        second = cache.get_or_create(
            "test-model",
            "Why can't my device connect?",
            provider,
        )

        self.assertEqual(first, second)
        self.assertEqual(provider.calls, 1)
        self.assertTrue(cache_path.exists())


class EmbeddingFilterTests(unittest.TestCase):
    def test_rejects_iframe_only_chunk(self) -> None:
        chunk = {
            "content": """
# Audit Log API

<iframe
  src="/assets/audit-log-api.html"
  width="100%">
</iframe>
"""
        }

        self.assertEqual(searchable_text(chunk["content"]), "")
        self.assertFalse(should_embed(chunk))

    def test_accepts_troubleshooting_content(self) -> None:
        chunk = {
            "content": """
## Quick diagnosis

Run `stctl device agent-status sensor-001`.
"""
        }

        self.assertTrue(should_embed(chunk))
        self.assertIn(
            "stctl device agent-status",
            searchable_text(chunk["content"]),
        )


if __name__ == "__main__":
    unittest.main()
