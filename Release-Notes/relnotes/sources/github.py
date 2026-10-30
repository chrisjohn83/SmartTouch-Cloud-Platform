"""GitHub adapter: merged pull requests in a date range (REST API).

Uses merged PRs rather than raw commits: PR titles are curated, carry labels,
and squash-merges make commits noisy. GitHub search returns at most 1,000 PRs
per query, which is plenty for one release window.
"""
from __future__ import annotations

import requests

from ..models import ChangeItem, find_jira_keys
from .http import env, request

API = "https://api.github.com"


def _session(cfg: dict) -> requests.Session:
    s = requests.Session()
    s.headers.update({"Accept": "application/vnd.github+json",
                      "X-GitHub-Api-Version": "2022-11-28"})
    token = env(cfg.get("token_env", "GITHUB_TOKEN"), required=False)
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    return s


def fetch(cfg: dict, since: str, until: str) -> list[ChangeItem]:
    api = cfg.get("api_url", API).rstrip("/")   # GitHub Enterprise: https://ghe.example.com/api/v3
    repo = cfg["repo"]
    s = _session(cfg)
    q = f"repo:{repo} is:pr is:merged merged:{since}..{until}"
    if cfg.get("base"):
        q += f" base:{cfg['base']}"

    items, page = [], 1
    while True:
        data = request(s, f"{api}/search/issues",
                       params={"q": q, "per_page": 100, "page": page}).json()
        for pr in data.get("items", []):
            files = _files(s, api, repo, pr["number"]) if cfg.get("fetch_files", True) else []
            items.append(parse_pr(pr, files))
        if len(data.get("items", [])) < 100 or page >= 10:
            break
        page += 1
    return items


def _files(s, api, repo, number) -> list[str]:
    out, page = [], 1
    while True:
        batch = request(s, f"{api}/repos/{repo}/pulls/{number}/files",
                        params={"per_page": 100, "page": page}).json()
        out += [f["filename"] for f in batch]
        if len(batch) < 100:
            return out
        page += 1


def parse_pr(pr: dict, files: list[str]) -> ChangeItem:
    body = pr.get("body") or ""
    return ChangeItem(
        id=f"github:#{pr['number']}",
        source="github",
        title=pr["title"].strip(),
        body=body[:2000],
        author=(pr.get("user") or {}).get("login", ""),
        url=pr["html_url"],
        files=files,
        labels=[l["name"] for l in pr.get("labels", [])],
        jira_keys=find_jira_keys(f"{pr['title']}\n{body}"),
        merged_at=(pr.get("pull_request") or {}).get("merged_at") or pr.get("closed_at") or "",
    )


def fetch_known_issues(cfg: dict, version: str) -> list[ChangeItem]:
    """Open GitHub issues carrying the known-issue label (off when label is unset)."""
    label = cfg.get("known_issue_label")
    if not label:
        return []
    api = cfg.get("api_url", API).rstrip("/")
    s = _session(cfg)
    q = f'repo:{cfg["repo"]} is:issue is:open label:"{label}"'
    data = request(s, f"{api}/search/issues", params={"q": q, "per_page": 100}).json()
    return [parse_issue(i) for i in data.get("items", [])]


def parse_issue(issue: dict) -> ChangeItem:
    body = issue.get("body") or ""
    return ChangeItem(
        id=f"github:issue#{issue['number']}", source="github", kind="known_issue",
        title=issue["title"].strip(), body=body[:2000],
        author=(issue.get("user") or {}).get("login", ""), url=issue["html_url"],
        labels=[l["name"] for l in issue.get("labels", [])],
        jira_keys=find_jira_keys(f"{issue['title']}\n{body}"),
    )
