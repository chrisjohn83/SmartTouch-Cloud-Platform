"""Keyword/decision-tree classifier for the four standard categories.

Two jobs: (1) an offline fallback when no API key is set, and (2) a
deterministic 'second opinion' — when it confidently disagrees with the model,
the item goes to the human review queue.
"""
from __future__ import annotations

import re

from .models import ChangeItem

FEAT, ENH, BUG, DOC = "New Features", "Enhancements", "Bug Fixes", "Documentation"

CONVENTIONAL = {"feat": FEAT, "fix": BUG, "docs": DOC, "doc": DOC, "perf": ENH, "refactor": ENH}
FEATURE_VERBS = {"add", "adds", "added", "new", "create", "creates", "introduce", "introduces",
                 "implement", "implements", "launch", "enable"}
ENH_WORDS = {"improve", "improves", "improved", "update", "updates", "enhance", "enhanced", "optimize",
             "optimise", "increase", "better", "refactor", "faster", "reduce", "redesign", "speed",
             "simplify", "upgrade", "streamline"}
BUG_WORDS = {"fix", "fixes", "fixed", "bug", "resolve", "resolves", "resolved", "correct", "corrects",
             "repair", "hotfix", "patch", "crash", "regression"}
STRONG_DOC = {"docs", "documentation", "readme", "typo", "typos", "changelog"}
WEAK_DOC = {"guide", "tutorial", "docstring"}
DOC_PATH = re.compile(r"(^|/)(docs?|documentation)/|\.(md|mdx|rst|adoc)$", re.I)


def clean_title(title: str) -> str:
    t = re.sub(r"^\s*\w+(\([^)]*\))?!?:\s*", "", title)            # conventional prefix
    t = re.sub(r"^\s*(\[?[A-Z][A-Z0-9]+-\d+\]?[:\s-]*)+", "", t)   # leading Jira keys
    t = t.strip(" -:")
    return t[:1].upper() + t[1:] if t else title


def classify(item: ChangeItem) -> tuple[str, float, str]:
    raw = item.title.strip().lower()
    m = re.match(r"^(\w+)(\([^)]*\))?!?:", raw)
    if m and m.group(1) in CONVENTIONAL:
        return CONVENTIONAL[m.group(1)], 0.85, "conventional-commit prefix"

    if item.files and all(DOC_PATH.search(f) for f in item.files):
        return DOC, 0.9, "only documentation files changed"

    itype = (item.issue_type or "").lower()
    if itype == "bug":
        return BUG, 0.9, "Jira issue type Bug"

    words = re.findall(r"[a-z]+", clean_title(item.title).lower())
    first = words[0] if words else ""
    if STRONG_DOC & set(words) or (first in FEATURE_VERBS | ENH_WORDS and WEAK_DOC & set(words)):
        return DOC, 0.75, "documentation keyword"
    if first in BUG_WORDS or BUG_WORDS & set(words[:3]):
        return BUG, 0.75, "bug-fix keyword"
    if first in FEATURE_VERBS:
        if ENH_WORDS & set(words[1:4]):
            return ENH, 0.65, "'add' + improvement word → improves existing"
        return FEAT, 0.65, "new-capability verb"
    if first in ENH_WORDS or ENH_WORDS & set(words):
        return ENH, 0.7, "improvement keyword"
    if itype in {"story", "new feature", "epic", "feature"}:
        return FEAT, 0.6, f"Jira issue type {item.issue_type}"
    if itype in {"improvement", "enhancement"}:
        return ENH, 0.7, f"Jira issue type {item.issue_type}"
    return ENH, 0.4, "default: unsure → Enhancement"


# ---------- offline title + description (the LLM writes these when online) ----------

KEY_LINE = re.compile(r"^\s*(fixes|closes|implements|resolves|refs?|for|see|part of)\s+"
                      r"[A-Z][A-Z0-9]+-\d+[.\s]*$", re.I | re.M)
INLINE_KEY = re.compile(r"\s*\(?\b[A-Z][A-Z0-9]+-\d+\b\)?")


def first_sentences(text: str, max_words: int = 30) -> str:
    t = KEY_LINE.sub("", text or "")
    t = INLINE_KEY.sub("", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return ""
    out: list[str] = []
    for s in re.split(r"(?<=[.!?])\s+", t):
        if out and len(" ".join(out + [s]).split()) > max_words:
            break
        out.append(s)
    res = " ".join(out).strip()
    return res if res.endswith((".", "!", "?")) else res + "."


def describe(item: ChangeItem, category: str, max_words: int = 30) -> tuple[str, str]:
    """Best-effort user-facing (title, description) from source text only."""
    title = clean_title(item.title)
    if item.release_note:
        return title, first_sentences(item.release_note, max_words)
    if item.kind == "known_issue":
        return title, first_sentences(item.body, max_words)
    # Jira text usually states the problem; the linked PR states what changed.
    pr_texts = [r.get("body", "") for r in item.related]
    is_jira_bug = category == BUG and (item.issue_type or "").lower() == "bug"
    if is_jira_bug and item.related:
        title = clean_title(item.related[0]["title"])
    for t in pr_texts:
        if first_sentences(t):
            return title, first_sentences(t, max_words)
    if is_jira_bug:
        sym = first_sentences(item.body, max_words)
        return title, f"Resolved an issue: {sym}" if sym else ""
    for t in [item.body]:
        if first_sentences(t):
            return title, first_sentences(t, max_words)
    return title, ""
