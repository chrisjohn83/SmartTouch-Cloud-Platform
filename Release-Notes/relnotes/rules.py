"""Deterministic exclusion rules (the v4 'Exclusions' section, as code).

These run BEFORE the model sees anything: they are cheap, auditable, and
never drift. Each exclusion records which rule fired.
"""
from __future__ import annotations

import fnmatch
import re

from .models import ChangeItem, Decision


class Rules:
    def __init__(self, cfg: dict):
        self.keywords = [k.lower() for k in cfg.get("keywords", [])]
        self.prefixes = [p.lower() for p in cfg.get("prefixes", [])]
        self.only_paths = cfg.get("only_paths", [])
        self.bots = {b.lower() for b in cfg.get("bot_authors", [])}
        self.skip_labels = {l.lower() for l in cfg.get("skip_labels", [])}
        self.force_labels = {l.lower() for l in cfg.get("force_include_labels", [])}
        self.skip_issue_types = {t.lower() for t in cfg.get("skip_issue_types", [])}
        # word-boundary match so "temp" does not hit "template"
        self._kw = [(k, re.compile(rf"(?<![a-z0-9]){re.escape(k)}(?![a-z0-9])")) for k in self.keywords]

    def check(self, item: ChangeItem) -> str | None:
        """Return the reason an item is excluded, or None to keep it."""
        labels = {l.lower() for l in item.labels}
        if labels & self.force_labels:
            return None
        title = item.title.strip().lower()

        if item.author.lower() in self.bots or item.author.lower().endswith("[bot]"):
            return f"bot author ({item.author})"
        for p in self.prefixes:
            if title.startswith(p):
                return f"prefix '{p}'"
        for k, rx in self._kw:
            if rx.search(title):
                return f"keyword '{k}'"
        hit = labels & self.skip_labels
        if hit:
            return f"label '{sorted(hit)[0]}'"
        if item.issue_type and item.issue_type.lower() in self.skip_issue_types:
            return f"issue type '{item.issue_type}'"
        if item.files and all(self._internal_path(f) for f in item.files):
            return "only internal/test/lockfile paths changed"
        return None

    def _internal_path(self, path: str) -> bool:
        p = "/" + path.lstrip("/")
        return any(fnmatch.fnmatch(p, pat) or fnmatch.fnmatch(p.rsplit("/", 1)[-1], pat)
                   for pat in self.only_paths)

    def apply(self, items: list[ChangeItem]) -> dict[str, Decision]:
        out = {}
        for item in items:
            reason = self.check(item)
            if reason:
                out[item.id] = Decision(item.id, True, reason=reason, decided_by="rules")
        return out
