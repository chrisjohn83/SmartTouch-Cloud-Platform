from __future__ import annotations

import unittest

from ai_docs.import_postgres import (
    DIMENSIONS,
    prepare_record,
    vector_literal,
)
from ai_docs.postgres_search import (
    search_postgres,
    search_postgres_lexical,
)

class PostgresImportTests(unittest.TestCase):
    def test_vector_literal_formats_vector(self) -> None:
        vector = [0.0] * DIMENSIONS
        result = vector_literal(vector)

        self.assertTrue(result.startswith("["))
        self.assertTrue(result.endswith("]"))
        self.assertEqual(result.count(","), DIMENSIONS - 1)

    def test_vector_literal_rejects_wrong_dimensions(self) -> None:
        with self.assertRaisesRegex(ValueError, "Expected 1536"):
            vector_literal([0.1, 0.2, 0.3])

    def test_prepare_record_reads_nested_embedding(self) -> None:
        record = {
            "id": "chunk-1",
            "source_path": "guide.md",
            "source_url": "https://example.com/guide/",
            "title": "Guide",
            "heading": "Diagnosis",
            "heading_path": ["Guide", "Diagnosis"],
            "content": "Check the device.",
            "content_hash": "abc123",
            "chunk_index": 0,
            "start_line": 1,
            "end_line": 3,
            "word_count": 3,
            "metadata": {"persona": ["developer"]},
            "embedding": {
                "model": "text-embedding-3-small",
                "dimensions": DIMENSIONS,
                "vector": [0.0] * DIMENSIONS,
            },
        }

        prepared = prepare_record(record)

        self.assertEqual(prepared[0], "chunk-1")
        self.assertEqual(prepared[13], "text-embedding-3-small")
        self.assertEqual(prepared[14], DIMENSIONS)
        self.assertTrue(prepared[15].startswith("["))


class PostgresSearchTests(unittest.TestCase):
    def test_rejects_wrong_query_dimensions(self) -> None:
        with self.assertRaisesRegex(ValueError, "1536-dimensional"):
            search_postgres(
                [0.1, 0.2],
                database_url="postgresql://unused",
            )

    def test_rejects_invalid_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 1"):
            search_postgres(
                [0.0] * DIMENSIONS,
                database_url="postgresql://unused",
                limit=0,
        )
    def test_lexical_search_rejects_empty_query(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            search_postgres_lexical(
                "   ",
                database_url="postgresql://unused",
            )

    def test_lexical_search_rejects_invalid_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 1"):
            search_postgres_lexical(
                "session already open",
                database_url="postgresql://unused",
                limit=0,
            )

    def test_fuses_semantic_and_lexical_results(self) -> None:
        from ai_docs.postgres_search import fuse_postgres_results

        semantic = [
            {"id": "general", "score": 0.8},
            {"id": "exact-error", "score": 0.6},
        ]
        lexical = [
            {"id": "exact-error", "score": 1.1},
            {"id": "general", "score": 0.1},
        ]

        results = fuse_postgres_results(
            semantic,
            lexical,
            limit=2,
        )

        self.assertEqual(results[0]["id"], "exact-error")
        self.assertEqual(results[0]["lexical_rank"], 1)
        self.assertEqual(results[0]["semantic_rank"], 2)


if __name__ == "__main__":
    unittest.main()
