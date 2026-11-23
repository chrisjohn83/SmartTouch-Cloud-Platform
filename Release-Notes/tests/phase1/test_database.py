
"""Tests for the Phase 1 intake database."""

from app.database.database import connect, initialize_database


def test_initialize_database_creates_required_tables(tmp_path):
    database_path = tmp_path / "release_notes.db"

    initialize_database(database_path)

    with connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

    table_names = {row["name"] for row in rows}

    assert {
        "sources",
        "collection_runs",
        "source_checkpoints",
        "raw_items",
    }.issubset(table_names)


def test_database_enables_foreign_keys(tmp_path):
    database_path = tmp_path / "release_notes.db"

    initialize_database(database_path)

    with connect(database_path) as connection:
        enabled = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

    assert enabled == 1
