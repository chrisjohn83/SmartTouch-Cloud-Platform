"""Tests for raw intake storage and change detection."""

from app.database.database import connect, initialize_database
from app.database.repository import (
    register_source,
    start_collection_run,
    store_raw_item,
)


def test_raw_item_status_changes(tmp_path):
    database_path = tmp_path / "release_notes.db"
    initialize_database(database_path)

    with connect(database_path) as connection:
        register_source(connection, "github")
        run_id = start_collection_run(connection)

        original = {
            "number": 25,
            "title": "Add device monitoring",
        }

        first_status = store_raw_item(
            connection,
            run_id=run_id,
            source_name="github",
            source_id="pull-request:25",
            item_type="pull_request",
            title=original["title"],
            raw_payload=original,
        )

        unchanged_status = store_raw_item(
            connection,
            run_id=run_id,
            source_name="github",
            source_id="pull-request:25",
            item_type="pull_request",
            title=original["title"],
            raw_payload=original,
        )

        updated = {
            "number": 25,
            "title": "Add device health monitoring",
        }

        updated_status = store_raw_item(
            connection,
            run_id=run_id,
            source_name="github",
            source_id="pull-request:25",
            item_type="pull_request",
            title=updated["title"],
            raw_payload=updated,
        )

        count = connection.execute(
            "SELECT COUNT(*) FROM raw_items"
        ).fetchone()[0]

    assert first_status == "new"
    assert unchanged_status == "unchanged"
    assert updated_status == "updated"
    assert count == 1
    