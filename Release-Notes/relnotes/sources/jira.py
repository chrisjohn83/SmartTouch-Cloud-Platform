"""Jira Cloud adapter: issues completed in a window, or in a fixVersion.

Uses the enhanced search endpoint POST /rest/api/3/search/jql with
nextPageToken pagination (the older /rest/api/3/search is deprecated).
Auth: Atlassian account email + API token (basic auth).
"""
from __future__ import annotations

import requests

from ..models import ChangeItem
from .http import env, request


def build_jql(cfg: dict, since: str, until: str) -> str:
    if cfg.get("jql"):
        return cfg["jql"].format(since=since, until=until)
    project = cfg["project"]
    if cfg.get("fix_version"):
        return f'project = {project} AND fixVersion = "{cfg["fix_version"]}" ORDER BY key'
    return (f'project = {project} AND statusCategory = Done '
            f'AND resolved >= "{since}" AND resolved <= "{until} 23:59" ORDER BY key')


def fetch(cfg: dict, since: str, until: str) -> list[ChangeItem]:
    return _search(cfg, build_jql(cfg, since, until))


def fetch_known_issues(cfg: dict, version: str) -> list[ChangeItem]:
    """Open issues flagged as known issues (default: label known-issue, not Done)."""
    jql = cfg.get("known_issues_jql")
    if not jql:
        return []
    items = _search(cfg, jql.format(project=cfg["project"], version=version))
    for i in items:
        i.kind = "known_issue"
    return items


def _search(cfg: dict, jql: str) -> list[ChangeItem]:
    base = cfg["base_url"].rstrip("/")
    s = requests.Session()
    s.auth = (env(cfg.get("email_env", "JIRA_EMAIL")), env(cfg.get("token_env", "JIRA_API_TOKEN")))
    rn_field = cfg.get("release_note_field")
    fields = ["summary", "description", "issuetype", "labels", "assignee", "resolutiondate"]
    if rn_field:
        fields.append(rn_field)

    items, token = [], None
    while True:
        body = {"jql": jql, "fields": fields, "maxResults": 100}
        if token:
            body["nextPageToken"] = token
        data = request(s, f"{base}/rest/api/3/search/jql", method="POST", json_body=body).json()
        items += [parse_issue(i, base, rn_field) for i in data.get("issues", [])]
        token = data.get("nextPageToken")
        if not token or data.get("isLast", False):
            return items


def adf_text(node) -> str:
    """Flatten Atlassian Document Format (or plain string) into text."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return " ".join(adf_text(n) for n in node).strip()
    if node.get("type") == "text":
        return node.get("text", "")
    return " ".join(adf_text(c) for c in node.get("content", []) or []).strip()


def parse_issue(issue: dict, base: str, rn_field: str | None = None, kind: str = "change") -> ChangeItem:
    f = issue.get("fields", {})
    key = issue["key"]
    return ChangeItem(
        id=f"jira:{key}",
        source="jira",
        kind=kind,
        title=(f.get("summary") or "").strip(),
        body=adf_text(f.get("description"))[:2000],
        author=((f.get("assignee") or {}).get("displayName") or ""),
        url=f"{base}/browse/{key}",
        labels=f.get("labels") or [],
        issue_type=(f.get("issuetype") or {}).get("name"),
        jira_keys=[key],
        merged_at=f.get("resolutiondate") or "",
        release_note=adf_text(f.get(rn_field)) if rn_field else "",
    )
