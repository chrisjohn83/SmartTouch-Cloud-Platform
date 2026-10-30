"""Bitbucket Cloud adapter: merged pull requests (REST 2.0).

Auth: either a repository/workspace access token (BITBUCKET_ACCESS_TOKEN, sent as
Bearer) or an Atlassian account email + API token (basic auth).
Bitbucket has no merged_on filter, so updated_on is used as the window; PRs
updated after merge (comments) may appear in a later window too. For exact
windows, set `branch` and review the decisions file.
Bitbucket Data Center uses a different API (/rest/api/1.0) and needs its own adapter.
"""
from __future__ import annotations

import requests

from ..models import ChangeItem, find_jira_keys
from .http import env, request

API = "https://api.bitbucket.org/2.0"


def fetch(cfg: dict, since: str, until: str) -> list[ChangeItem]:
    ws, repo = cfg["workspace"], cfg["repo"]
    s = requests.Session()
    bearer = env(cfg.get("access_token_env", "BITBUCKET_ACCESS_TOKEN"), required=False)
    if bearer:
        s.headers["Authorization"] = f"Bearer {bearer}"
    else:
        s.auth = (env(cfg.get("email_env", "BITBUCKET_EMAIL")),
                  env(cfg.get("token_env", "BITBUCKET_API_TOKEN")))

    q = f'state = "MERGED" AND updated_on >= {since}T00:00:00+00:00 AND updated_on <= {until}T23:59:59+00:00'
    if cfg.get("branch"):
        q += f' AND destination.branch.name = "{cfg["branch"]}"'
    url = f"{API}/repositories/{ws}/{repo}/pullrequests"
    params = {"q": q, "pagelen": 50, "state": "MERGED"}

    items = []
    while url:
        data = request(s, url, params=params).json()
        params = None  # "next" URL already carries the query
        for pr in data.get("values", []):
            files = _files(s, ws, repo, pr["id"]) if cfg.get("fetch_files", True) else []
            items.append(parse_pr(pr, files))
        url = data.get("next")
    return items


def _files(s, ws, repo, pr_id) -> list[str]:
    out, url = [], f"{API}/repositories/{ws}/{repo}/pullrequests/{pr_id}/diffstat"
    while url:
        data = request(s, url).json()
        for d in data.get("values", []):
            path = (d.get("new") or d.get("old") or {}).get("path")
            if path:
                out.append(path)
        url = data.get("next")
    return out


def parse_pr(pr: dict, files: list[str]) -> ChangeItem:
    desc = pr.get("description") or (pr.get("summary") or {}).get("raw") or ""
    branch = ((pr.get("source") or {}).get("branch") or {}).get("name", "")
    return ChangeItem(
        id=f"bitbucket:#{pr['id']}",
        source="bitbucket",
        title=pr["title"].strip(),
        body=desc[:2000],
        author=(pr.get("author") or {}).get("display_name", ""),
        url=((pr.get("links") or {}).get("html") or {}).get("href", ""),
        files=files,
        jira_keys=find_jira_keys(f"{pr['title']}\n{desc}\n{branch}"),
        merged_at=pr.get("updated_on", ""),
    )
