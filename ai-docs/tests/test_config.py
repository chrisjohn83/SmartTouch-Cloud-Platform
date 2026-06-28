from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from ai_docs.config import (
    DEFAULT_ANSWER_MODEL,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_MAX_CONTEXT_CHARS,
    DEFAULT_RETRIEVAL_LIMIT,
    load_config,
)


class ConfigTests(unittest.TestCase):
    def test_loads_defaults(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            config = load_config()

        self.assertIsNone(config.database_url)
        self.assertEqual(config.embedding_model, DEFAULT_EMBEDDING_MODEL)
        self.assertEqual(config.answer_model, DEFAULT_ANSWER_MODEL)
        self.assertEqual(
            config.default_retrieval_limit,
            DEFAULT_RETRIEVAL_LIMIT,
        )
        self.assertEqual(config.max_context_chars, DEFAULT_MAX_CONTEXT_CHARS)

    def test_loads_environment_overrides(self) -> None:
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://example",
                "AI_DOCS_EMBEDDING_MODEL": "embedding-model",
                "AI_DOCS_ANSWER_MODEL": "answer-model",
                "AI_DOCS_DEFAULT_RETRIEVAL_LIMIT": "3",
                "AI_DOCS_MAX_CONTEXT_CHARS": "900",
            },
            clear=True,
        ):
            config = load_config()

        self.assertEqual(config.database_url, "postgresql://example")
        self.assertEqual(config.embedding_model, "embedding-model")
        self.assertEqual(config.answer_model, "answer-model")
        self.assertEqual(config.default_retrieval_limit, 3)
        self.assertEqual(config.max_context_chars, 900)

    def test_rejects_invalid_integer(self) -> None:
        with patch.dict(
            os.environ,
            {"AI_DOCS_DEFAULT_RETRIEVAL_LIMIT": "not-a-number"},
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "must be an integer"):
                load_config()

    def test_rejects_non_positive_integer(self) -> None:
        with patch.dict(
            os.environ,
            {"AI_DOCS_MAX_CONTEXT_CHARS": "0"},
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "must be at least 1"):
                load_config()


if __name__ == "__main__":
    unittest.main()
