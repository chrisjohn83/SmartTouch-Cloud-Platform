"""Database operations for sources and collection checkpoints."""

from __future__ import annotations

import json
import hashlib
import sqlite3
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


def register_source(
    connection: sqlite3.Connection,
    name: str,
    configuration: dict[str, Any] | None = None,
    enabled: bool = True,
) -> None:
    """Create or update a configured collection source."""

    now = utc_now()
    configuration_json = json.dumps(
        configuration or {},
        sort_keys=True,
    )

    connection.execute(
        """
        INSERT INTO sources (
            name,
            enabled,
            configuration_json,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            enabled = excluded.enabled,
            configuration_json = excluded.configuration_json,
            updated_at = excluded.updated_at
        """,
        (
            name,
            int(enabled),
            configuration_json,
            now,
            now,
        ),
    )

    connection.commit()


def get_checkpoint(
    connection: sqlite3.Connection,
    source_name: str,
) -> dict[str, Any] | None:
    """Return the latest checkpoint for a source."""

    row = connection.execute(
        """
        SELECT
            source_name,
            cursor_value,
            last_successful_sync,
            updated_at
        FROM source_checkpoints
        WHERE source_name = ?
        """,
        (source_name,),
    ).fetchone()

    return dict(row) if row else None


def update_checkpoint(
    connection: sqlite3.Connection,
    source_name: str,
    last_successful_sync: str,
    cursor_value: str | None = None,
) -> None:
    """Create or replace a source checkpoint."""

    connection.execute(
        """
        INSERT INTO source_checkpoints (
            source_name,
            cursor_value,
            last_successful_sync,
            updated_at
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(source_name) DO UPDATE SET
            cursor_value = excluded.cursor_value,
            last_successful_sync = excluded.last_successful_sync,
            updated_at = excluded.updated_at
        """,
        (
            source_name,
            cursor_value,
            last_successful_sync,
            utc_now(),
        ),
    )

    connection.commit()
def start_collection_run(
    connection: sqlite3.Connection,
    trigger_type: str = "manual",
) -> int:
    """Create a collection-run record and return its ID."""

    cursor = connection.execute(
        """
        INSERT INTO collection_runs (
            started_at,
            status,
            trigger_type
        )
        VALUES (?, 'running', ?)
        """,
        (utc_now(), trigger_type),
    )

    connection.commit()
    return int(cursor.lastrowid)


def finish_collection_run(
    connection: sqlite3.Connection,
    run_id: int,
    status: str,
    collected_count: int = 0,
    new_count: int = 0,
    updated_count: int = 0,
    unchanged_count: int = 0,
    error_message: str | None = None,
) -> None:
    """Complete a collection run and store its totals."""

    connection.execute(
        """
        UPDATE collection_runs
        SET
            completed_at = ?,
            status = ?,
            collected_count = ?,
            new_count = ?,
            updated_count = ?,
            unchanged_count = ?,
            error_message = ?
        WHERE id = ?
        """,
        (
            utc_now(),
            status,
            collected_count,
            new_count,
            updated_count,
            unchanged_count,
            error_message,
            run_id,
        ),
    )

    connection.commit()


def store_raw_item(
    connection: sqlite3.Connection,
    run_id: int,
    source_name: str,
    source_id: str,
    item_type: str,
    title: str,
    raw_payload: dict[str, Any],
    source_url: str | None = None,
    source_created_at: str | None = None,
    source_updated_at: str | None = None,
) -> str:
    """Store a raw record and return new, updated, or unchanged."""

    serialized_payload = json.dumps(
        raw_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    content_hash = hashlib.sha256(
        serialized_payload.encode("utf-8")
    ).hexdigest()

    existing = connection.execute(
        """
        SELECT content_hash
        FROM raw_items
        WHERE source_name = ? AND source_id = ?
        """,
        (source_name, source_id),
    ).fetchone()

    now = utc_now()

    if existing is None:
        collection_status = "new"

        connection.execute(
            """
            INSERT INTO raw_items (
                source_name,
                source_id,
                source_url,
                item_type,
                title,
                raw_json,
                source_created_at,
                source_updated_at,
                content_hash,
                first_seen_at,
                last_seen_at,
                collection_status,
                collection_run_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_name,
                source_id,
                source_url,
                item_type,
                title,
                serialized_payload,
                source_created_at,
                source_updated_at,
                content_hash,
                now,
                now,
                collection_status,
                run_id,
            ),
        )
    else:
        collection_status = (
            "unchanged"
            if existing["content_hash"] == content_hash
            else "updated"
        )

        connection.execute(
            """
            UPDATE raw_items
            SET
                source_url = ?,
                item_type = ?,
                title = ?,
                raw_json = ?,
                source_created_at = ?,
                source_updated_at = ?,
                content_hash = ?,
                last_seen_at = ?,
                collection_status = ?,
                collection_run_id = ?
            WHERE source_name = ? AND source_id = ?
            """,
            (
                source_url,
                item_type,
                title,
                serialized_payload,
                source_created_at,
                source_updated_at,
                content_hash,
                now,
                collection_status,
                run_id,
                source_name,
                source_id,
            ),
        )

    connection.commit()
    return collection_status
