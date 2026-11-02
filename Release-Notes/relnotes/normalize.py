"""Cross-source linking: collapse PRs into the Jira issue they implement.

A Jira issue is the canonical, customer-facing unit of work; its PRs (GitHub or
Bitbucket) become `related` evidence. PRs whose Jira issue was excluded are
excluded too, so internal work cannot leak in through its code changes.
Known issues pass through unchanged (they are open work, not shipped changes).
"""
from __future__ import annotations

from .models import ChangeItem, Decision


def link_and_merge(items: list[ChangeItem], excluded: dict[str, Decision]
                   ) -> tuple[list[ChangeItem], dict[str, Decision]]:
    known = [i for i in items if i.kind == "known_issue" and i.id not in excluded]
    items = [i for i in items if i.kind == "change"]
    jira_by_key = {i.ref: i for i in items if i.source == "jira"}
    excluded_keys = {i.ref for i in items if i.source == "jira" and i.id in excluded}
    extra: dict[str, Decision] = {}
    candidates: list[ChangeItem] = []

    for item in items:
        if item.id in excluded or item.source == "jira":
            continue
        keys = item.jira_keys
        if keys and all(k in excluded_keys for k in keys):
            extra[item.id] = Decision(item.id, True, reason=f"linked to excluded {', '.join(keys)}",
                                      decided_by="rules")
            continue
        parent = next((jira_by_key[k] for k in keys if k in jira_by_key and k not in excluded_keys), None)
        if parent is not None:
            parent.related.append({"id": item.id, "title": item.title, "url": item.url, "body": item.body})
            parent.files += [f for f in item.files if f not in parent.files]
        else:
            candidates.append(item)

    jira_kept = [i for i in items if i.source == "jira" and i.id not in excluded]
    return jira_kept + candidates + known, extra
