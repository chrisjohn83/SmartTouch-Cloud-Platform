"""Tests for Phase 1 collection orchestration."""

from datetime import datetime, timezone

import pytest

from app.collection.service import run_github_collection
from app.database.database import connect
from app.database.repository import get_checkpoint


def phase1_configuration():
    return {
        "database": {
            "type": "sqlite",
            "path": "data/release_notes.db",
        },
        "collection": {
            "default_lookback_days": 30,
            "overlap_minutes": 10,
        },
        "sources": {
            "github": {
                "enabled": True,
                "repository": (
                    "chrisjohn83/"
                    "SmartTouch-Cloud-Platform"
                ),
                "base_branch": "main",
                "known_issue_label": "known-issue",
            }
        },
    }


def fake_pull_requests(config, since):
    return [
        {
            "number": 52,
            "title": "Add device health monitoring",
            "html_url": "https://github.example/pull/52",
            "created_at": "2026-11-19T08:00:00Z",
            "updated_at": "2026-11-19T09:00:00Z",
            "merged_at": "2026-11-19T09:00:00Z",
        }
    ]


def fake_known_issues(config, since):
    return [
        {
            "number": 61,
            "title": "Device status can be delayed",
            "html_url": "https://github.example/issues/61",
            "created_at": "2026-11-19T08:00:00Z",
            "updated_at": "2026-11-19T09:00:00Z",
            "state": "open",
        }
    ]


def test_collection_stores_records_and_checkpoint(tmp_path):
    database_path = tmp_path / "release_notes.db"
    now = datetime(
        2026,
        11,
        20,
        10,
        0,
        tzinfo=timezone.utc,
    )

    result = run_github_collection(
        configuration=phase1_configuration(),
        database_path=database_path,
        collection_until=now,
        pull_request_fetcher=fake_pull_requests,
        known_issue_fetcher=fake_known_issues,
    )

    assert result["collected"] == 2
    assert result["new"] == 2

    with connect(database_path) as connection:
        checkpoint = get_checkpoint(connection, "github")
        item_count = connection.execute(
            "SELECT COUNT(*) FROM raw_items"
        ).fetchone()[0]

    assert item_count == 2
    assert checkpoint is not None
    assert checkpoint["last_successful_sync"] == now.isoformat()


def test_second_collection_detects_unchanged_items(tmp_path):
    database_path = tmp_path / "release_notes.db"

    first_time = datetime(
        2026,
        11,
        20,
        10,
        0,
        tzinfo=timezone.utc,
    )

    second_time = datetime(
        2026,
        11,
        20,
        12,
        0,
        tzinfo=timezone.utc,
    )

    arguments = {
        "configuration": phase1_configuration(),
        "database_path": database_path,
        "pull_request_fetcher": fake_pull_requests,
        "known_issue_fetcher": fake_known_issues,
    }

    run_github_collection(
        **arguments,
        collection_until=first_time,
    )

    result = run_github_collection(
        **arguments,
        collection_until=second_time,
    )

    assert result["collected"] == 2
    assert result["unchanged"] == 2
    assert result["new"] == 0


def test_failed_collection_does_not_update_checkpoint(tmp_path):
    database_path = tmp_path / "release_notes.db"

    def failing_fetcher(config, since):
        raise RuntimeError("GitHub unavailable")

    with pytest.raises(RuntimeError):
        run_github_collection(
            configuration=phase1_configuration(),
            database_path=database_path,
            pull_request_fetcher=failing_fetcher,
            known_issue_fetcher=fake_known_issues,
        )

    with connect(database_path) as connection:
        checkpoint = get_checkpoint(connection, "github")

        run_status = connection.execute(
            """
            SELECT status
            FROM collection_runs
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()["status"]

    assert checkpoint is None
    assert run_status == "failed"
