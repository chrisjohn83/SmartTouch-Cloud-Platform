"""Tests for the Phase 1 GitHub collector."""

from app.collection.collectors.github import (
    fetch_known_issues,
    fetch_merged_pull_requests,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.headers = {}

    def get(self, url, params, timeout):
        self.calls.append(
            {
                "url": url,
                "params": params,
                "timeout": timeout,
            }
        )

        return FakeResponse(self.responses.pop(0))


def github_config():
    return {
        "repository": "chrisjohn83/SmartTouch-Cloud-Platform",
        "base_branch": "main",
        "known_issue_label": "known-issue",
    }


def test_fetches_only_merged_pull_requests_after_checkpoint():
    session = FakeSession(
        [
            [
                {
                    "number": 30,
                    "title": "Add device monitoring",
                    "updated_at": "2026-11-19T12:00:00Z",
                    "merged_at": "2026-11-19T11:00:00Z",
                },
                {
                    "number": 29,
                    "title": "Unmerged work",
                    "updated_at": "2026-11-19T11:00:00Z",
                    "merged_at": None,
                },
                {
                    "number": 28,
                    "title": "Older merged work",
                    "updated_at": "2026-11-19T09:00:00Z",
                    "merged_at": "2026-11-19T08:00:00Z",
                },
            ]
        ]
    )

    results = fetch_merged_pull_requests(
        github_config(),
        since="2026-11-19T10:00:00+00:00",
        session=session,
    )

    assert len(results) == 1
    assert results[0]["number"] == 30


def test_known_issues_exclude_pull_requests():
    session = FakeSession(
        [
            [
                {
                    "number": 41,
                    "title": "Device status can be delayed",
                    "state": "open",
                },
                {
                    "number": 42,
                    "title": "Closed known issue",
                    "state": "closed",
                },
                {
                    "number": 43,
                    "title": "A pull request",
                    "pull_request": {
                        "url": "https://api.github.com/pulls/43"
                    },
                },
            ]
        ]
    )

    results = fetch_known_issues(
        github_config(),
        since="2026-11-19T10:00:00+00:00",
        session=session,
    )

    assert [issue["number"] for issue in results] == [41, 42]
