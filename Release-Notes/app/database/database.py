"""SQLite database setup for Phase 1 collection."""

from __future__ import annotations

import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "release_notes.db"

INITIAL_MIGRATION_PATH = (
    PROJECT_ROOT
    / "app"
    / "database"
    / "migrations"
    / "001_initial_schema.sql"
)


def connect(database_path: Path = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    """Open the database and enable SQLite foreign-key validation."""

    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database(
    database_path: Path = DEFAULT_DATABASE_PATH,
    migration_path: Path = INITIAL_MIGRATION_PATH,
) -> Path:
    """Create the Phase 1 tables and indexes."""

    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")

    schema = migration_path.read_text(encoding="utf-8")

    with connect(database_path) as connection:
        connection.executescript(schema)

    return database_path


if __name__ == "__main__":
    created_path = initialize_database()
    print(f"Database initialized: {created_path}")
