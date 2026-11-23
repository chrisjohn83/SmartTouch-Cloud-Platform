"""Tests for source registration and checkpoint storage."""

from app.database.database import connect, initialize_database
from app.database.repository import (
    get_checkpoint,
    register_source,
    update_checkpoint,
)


def test_register_source_and_store_checkpoint(tmp_path):
    database_path = tmp_path / "release_notes.db"
    initialize_database(database_path)

    with connect(database_path) as connection:
        register_source(
            connection,
            "github",
            {
                "repository": "chrisjohn83/SmartTouch-Cloud-Platform",
                "base_branch": "main",
            },
        )

        update_checkpoint(
            connection,
            source_name="github",
            last_successful_sync="2026-11-18T10:00:00+00:00",
            cursor_value="page-1",
        )

        checkpoint = get_checkpoint(connection, "github")

    assert checkpoint is not None
    assert checkpoint["source_name"] == "github"
    assert checkpoint["cursor_value"] == "page-1"
    assert (
        checkpoint["last_successful_sync"]
        == "2026-11-18T10:00:00+00:00"
    )


def test_checkpoint_can_be_updated(tmp_path):
    database_path = tmp_path / "release_notes.db"
    initialize_database(database_path)

    with connect(database_path) as connection:
        register_source(connection, "jira")

        update_checkpoint(
            connection,
            source_name="jira",
            last_successful_sync="2026-11-18T10:00:00+00:00",
        )

        update_checkpoint(
            connection,
            source_name="jira",
            last_successful_sync="2026-11-18T12:00:00+00:00",
            cursor_value="next-page",
        )

        checkpoint = get_checkpoint(connection, "jira")

    assert checkpoint is not None
    assert checkpoint["cursor_value"] == "next-page"
    assert (
        checkpoint["last_successful_sync"]
        == "2026-11-18T12:00:00+00:00"
    )
