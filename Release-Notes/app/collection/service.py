"""Phase 1 collection-service orchestration."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from app.collection.collectors.github import (
    fetch_known_issues,
    fetch_merged_pull_requests,
)
from app.configuration import load_configuration
from app.database.database import (
    DEFAULT_DATABASE_PATH,
    connect,
    initialize_database,
)
from app.database.repository import (
    finish_collection_run,
    get_checkpoint,
    register_source,
    start_collection_run,
    store_raw_item,
    update_checkpoint,
)


FetchFunction = Callable[
    [dict[str, Any], str],
    list[dict[str, Any]],
]


def calculate_collection_start(
    configuration: dict[str, Any],
    checkpoint: dict[str, Any] | None,
    collection_until: datetime,
) -> str:
    """Calculate the starting timestamp for a collection."""

    collection_settings = configuration.get("collection", {})
    overlap_minutes = collection_settings.get("overlap_minutes", 10)

    if checkpoint and checkpoint.get("last_successful_sync"):
        checkpoint_time = datetime.fromisoformat(
            checkpoint["last_successful_sync"]
        )

        start = checkpoint_time - timedelta(
            minutes=overlap_minutes
        )
    else:
        lookback_days = collection_settings.get(
            "default_lookback_days",
            30,
        )

        start = collection_until - timedelta(days=lookback_days)

    return start.astimezone(timezone.utc).isoformat()


def store_github_records(
    connection,
    run_id: int,
    pull_requests: list[dict[str, Any]],
    known_issues: list[dict[str, Any]],
) -> Counter:
    """Store GitHub records and count their change statuses."""

    counts: Counter = Counter()

    for pull_request in pull_requests:
        status = store_raw_item(
            connection,
            run_id=run_id,
            source_name="github",
            source_id=f"pull-request:{pull_request['number']}",
            item_type="pull_request",
            title=pull_request["title"],
            raw_payload=pull_request,
            source_url=pull_request.get("html_url"),
            source_created_at=pull_request.get("created_at"),
            source_updated_at=pull_request.get("updated_at"),
        )

        counts[status] += 1

    for issue in known_issues:
        status = store_raw_item(
            connection,
            run_id=run_id,
            source_name="github",
            source_id=f"issue:{issue['number']}",
            item_type="known_issue",
            title=issue["title"],
            raw_payload=issue,
            source_url=issue.get("html_url"),
            source_created_at=issue.get("created_at"),
            source_updated_at=issue.get("updated_at"),
        )

        counts[status] += 1

    return counts


def run_github_collection(
    configuration: dict[str, Any] | None = None,
    database_path: Path = DEFAULT_DATABASE_PATH,
    collection_until: datetime | None = None,
    pull_request_fetcher: FetchFunction = fetch_merged_pull_requests,
    known_issue_fetcher: FetchFunction = fetch_known_issues,
) -> dict[str, Any]:
    """Run one incremental GitHub collection."""

    settings = configuration or load_configuration()
    github_config = settings["sources"]["github"]

    if not github_config.get("enabled", False):
        raise ValueError("GitHub source is disabled.")

    until = collection_until or datetime.now(timezone.utc)

    if until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)

    initialize_database(database_path)

    with connect(database_path) as connection:
        register_source(
            connection,
            name="github",
            configuration=github_config,
            enabled=True,
        )

        checkpoint = get_checkpoint(connection, "github")

        since = calculate_collection_start(
            settings,
            checkpoint,
            until,
        )

        run_id = start_collection_run(
            connection,
            trigger_type="manual",
        )

        try:
            pull_requests = pull_request_fetcher(
                github_config,
                since,
            )

            known_issues = known_issue_fetcher(
                github_config,
                since,
            )

            counts = store_github_records(
                connection,
                run_id,
                pull_requests,
                known_issues,
            )

            total = sum(counts.values())

            finish_collection_run(
                connection,
                run_id=run_id,
                status="completed",
                collected_count=total,
                new_count=counts["new"],
                updated_count=counts["updated"],
                unchanged_count=counts["unchanged"],
            )

            checkpoint_time = until.astimezone(
                timezone.utc
            ).isoformat()

            update_checkpoint(
                connection,
                source_name="github",
                last_successful_sync=checkpoint_time,
            )

        except Exception as error:
            finish_collection_run(
                connection,
                run_id=run_id,
                status="failed",
                error_message=str(error),
            )

            raise

    return {
        "run_id": run_id,
        "source": "github",
        "since": since,
        "until": checkpoint_time,
        "collected": total,
        "new": counts["new"],
        "updated": counts["updated"],
        "unchanged": counts["unchanged"],
    }


if __name__ == "__main__":
    result = run_github_collection()
    print(json.dumps(result, indent=2))
