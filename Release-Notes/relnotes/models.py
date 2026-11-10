from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

JIRA_KEY_RE = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b")
EXCLUDED = "EXCLUDED"


def find_jira_keys(text: str) -> list[str]:
    seen: list[str] = []
    for k in JIRA_KEY_RE.findall(text or ""):
        if k not in seen:
            seen.append(k)
    return seen


@dataclass
class ChangeItem:
    """One change from any source, normalized."""
    id: str                      # e.g. "github:#101", "jira:PLAT-210", "bitbucket:#41"
    source: str                  # github | jira | bitbucket
    title: str
    kind: str = "change"         # change | known_issue
    body: str = ""
    author: str = ""
    url: str = ""
    files: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    issue_type: str | None = None
    jira_keys: list[str] = field(default_factory=list)
    merged_at: str = ""
    release_note: str = ""       # curated text from a Jira "Release Note" field, if any
    related: list[dict] = field(default_factory=list)  # linked PRs merged into this item

    @property
    def ref(self) -> str:
        return self.id.split(":", 1)[1]

    def to_prompt_dict(self) -> dict:
        d = {
            "id": self.id,
            "kind": self.kind,
            "source": self.source,
            "title": self.title,
            "description": (self.body or "")[:800],
        }
        if self.issue_type:
            d["jira_issue_type"] = self.issue_type
        if self.labels:
            d["labels"] = self.labels
        if self.release_note:
            d["release_note_field"] = self.release_note
        if self.files:
            d["files_changed"] = self.files[:15]
        if self.related:
            d["linked_pull_requests"] = [{"title": r["title"], "description": (r.get("body") or "")[:400]}
                                         for r in self.related]
        return d

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ChangeItem":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


@dataclass
class Decision:
    id: str
    excluded: bool
    category: str | None = None
    reason: str = ""
    description: str = ""
    title: str = ""
    confidence: float = 1.0
    decided_by: str = "llm"      # rules | llm | heuristic
    second_opinion: str | None = None  # heuristic category, used for cross-checking

    def to_dict(self) -> dict:
        return asdict(self)
