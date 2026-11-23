"""GitHub REST API collector for Phase 1."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests


DEFAULT_API_URL = "https://api.github.com"


def parse_timestamp(value: str) -> datetime:
    """Convert a GitHub timestamp into a timezone-aware datetime."""

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed


def create_session(config: dict[str, Any]) -> requests.Session:
    """Create an authenticated GitHub HTTP session."""

    session = requests.Session()

    session.headers.update(
        {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "smarttouch-release-notes",
        }
    )

    token_variable = config.get("token_env", "GITHUB_TOKEN")
    token = os.environ.get(token_variable)

    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    return session


def fetch_merged_pull_requests(
    config: dict[str, Any],
    since: str,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """Collect merged pull requests changed after the checkpoint."""

    http = session or create_session(config)

    repository = config["repository"]
    base_branch = config.get("base_branch", "main")
    api_url = config.get("api_url", DEFAULT_API_URL).rstrip("/")
    endpoint = f"{api_url}/repos/{repository}/pulls"

    checkpoint = parse_timestamp(since)
    collected: list[dict[str, Any]] = []
    page = 1

    while True:
        response = http.get(
            endpoint,
            params={
                "state": "closed",
                "base": base_branch,
                "sort": "updated",
                "direction": "desc",
                "per_page": 100,
                "page": page,
            },
            timeout=30,
        )
        response.raise_for_status()

        batch = response.json()
        reached_checkpoint = False

        for pull_request in batch:
            updated_at = parse_timestamp(pull_request["updated_at"])

            if updated_at <= checkpoint:
                reached_checkpoint = True
                break

            if pull_request.get("merged_at"):
                collected.append(pull_request)

        if reached_checkpoint or len(batch) < 100:
            break

        page += 1

    return collected


def fetch_known_issues(
    config: dict[str, Any],
    since: str,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """Collect changed issues carrying the known-issue label."""

    label = config.get("known_issue_label")

    if not label:
        return []

    http = session or create_session(config)

    repository = config["repository"]
    api_url = config.get("api_url", DEFAULT_API_URL).rstrip("/")
    endpoint = f"{api_url}/repos/{repository}/issues"

    collected: list[dict[str, Any]] = []
    page = 1

    while True:
        response = http.get(
            endpoint,
            params={
                "state": "all",
                "labels": label,
                "since": since,
                "sort": "updated",
                "direction": "asc",
                "per_page": 100,
                "page": page,
            },
            timeout=30,
        )
        response.raise_for_status()

        batch = response.json()

        for issue in batch:
            # GitHub's issues endpoint also returns pull requests.
            if "pull_request" not in issue:
                collected.append(issue)

        if len(batch) < 100:
            break

        page += 1

    return collected
