"""Quality gates for extracted data and the generated notes.

ERROR   = blocks publishing (CI exits non-zero)
WARNING = goes to the human review queue
"""
from __future__ import annotations

import datetime as dt
import re
from collections import Counter
from dataclasses import dataclass

from . import template
from .models import ChangeItem, Decision
from .render import KNOWN
from .rules import Rules

ERROR, WARN = "ERROR", "WARNING"
NUM_RE = re.compile(r"\d+(?:[.,]\d+)?%?")
KEY_OR_PATH = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b|[\w-]+/[\w./-]+\.\w+|#\d+")


@dataclass
class Finding:
    level: str
    check: str
    message: str
    item_id: str = ""


def validate(items: dict[str, ChangeItem], decisions: list[Decision], rules: Rules, cfg: dict,
             notes: str, tmpl: str, data: dict, omitted: list[str], raw_count: int) -> list[Finding]:
    q = cfg["quality"]
    cats = [c["name"] for c in cfg["categories"]] + [KNOWN]
    bug_cat = cfg["categories"][2]["name"] if len(cfg["categories"]) > 2 else None
    f: list[Finding] = []
    llm_side = [d for d in decisions if d.decided_by != "rules"]

    # V01 coverage — every candidate decided exactly once, no invented ids
    counts = Counter(d.id for d in llm_side)
    for iid in items:
        if counts[iid] == 0:
            f.append(Finding(ERROR, "V01 coverage", "candidate has no decision (dropped by model)", iid))
        elif counts[iid] > 1:
            f.append(Finding(ERROR, "V01 coverage", f"decided {counts[iid]} times", iid))
    for iid in counts:
        if iid not in items:
            f.append(Finding(ERROR, "V01 coverage", "decision for an id that was never extracted", iid))

    for d in llm_side:
        if d.id not in items:
            continue
        it = items[d.id]
        if d.excluded:
            level = WARN
            f.append(Finding(level, "V12 model exclusion",
                             f"model excluded a {it.kind.replace('_', ' ')}: {d.reason or 'no reason given'}", d.id))
            continue
        # V02 category valid and consistent with intake
        if d.category not in cats:
            f.append(Finding(ERROR, "V02 category", f"unknown category '{d.category}'", d.id))
        if (it.kind == "known_issue") != (d.category == KNOWN):
            f.append(Finding(ERROR, "V02 category",
                             f"{it.kind} placed in '{d.category}' (known issues come only from known-issue intake)", d.id))
        # V03 exclusion leakage — re-run deterministic rules on what will be published
        leak = rules.check(it) or rules.check(ChangeItem(it.id, it.source, d.title or it.title))
        if leak:
            f.append(Finding(ERROR, "V03 leakage", f"included item matches exclusion rule: {leak}", d.id))
        # V04 cross-source consistency
        itype = (it.issue_type or "").lower()
        if it.kind == "change" and itype == "bug" and bug_cat and d.category != bug_cat:
            f.append(Finding(WARN, "V04 consistency", f"Jira Bug placed in '{d.category}'", d.id))
        if itype in {"story", "new feature"} and d.category == bug_cat:
            f.append(Finding(WARN, "V04 consistency", f"Jira {it.issue_type} placed in '{bug_cat}'", d.id))
        # V05 second opinion
        if d.second_opinion and d.second_opinion != d.category and d.decided_by == "llm":
            f.append(Finding(WARN, "V05 second opinion",
                             f"model says '{d.category}', rules classifier says '{d.second_opinion}'", d.id))
        # V06 confidence
        if d.confidence < q.get("min_confidence", 0.6):
            f.append(Finding(WARN, "V06 confidence", f"low confidence {d.confidence:.2f}", d.id))
        # V07 title + description
        f += _check_text(d, it, q)
        # V08 traceability
        if not it.url:
            f.append(Finding(ERROR, "V08 traceability", "no source link", d.id))

    # V09 duplicates
    for sec, entries in data.items():
        if isinstance(entries, list):
            for t, n in Counter(e["title"].lower() for e in entries).items():
                if n > 1:
                    f.append(Finding(WARN, "V09 duplicate", f"'{t}' appears {n} times in {sec}"))

    # V10 template conformance (structure of the rendered document)
    f += check_template(notes, tmpl, cfg)

    # V11 volume sanity
    published = sum(len(v) for v in data.values() if isinstance(v, list))
    changes = sum(len(data.get(s, [])) for s, c in cfg["template"]["sections"].items() if KNOWN not in c)
    if changes == 0:
        f.append(Finding(WARN, "V11 volume", "no features or fixes — check date range and filters"))
    elif raw_count and 1 - published / raw_count > q.get("max_exclusion_rate", 0.7):
        f.append(Finding(WARN, "V11 volume", f"{1 - published / raw_count:.0%} of extracted items not published"))

    # V13 a known issue that this release also claims to fix
    fixed_keys = {k for d in llm_side if not d.excluded and d.id in items and d.category == bug_cat
                  for k in items[d.id].jira_keys}
    for d in llm_side:
        if d.id in items and d.category == KNOWN and set(items[d.id].jira_keys) & fixed_keys:
            f.append(Finding(ERROR, "V13 known vs fixed",
                             "listed as a known issue and also as a bug fix in this release", d.id))

    # V14 changes whose category has no section in the template
    for iid in omitted:
        d = next(x for x in llm_side if x.id == iid)
        f.append(Finding(WARN, "V14 omitted",
                         f"'{d.category}' has no section in the template — not published", iid))
    return f


def _check_text(d: Decision, it: ChangeItem, q: dict) -> list[Finding]:
    f = []
    title, desc = (d.title or "").strip(), (d.description or "").strip()
    if not desc:
        f.append(Finding(ERROR, "V07 description", "missing description (template needs '{title}: {description}')", d.id))
    else:
        words = len(desc.split())
        if words > q.get("max_summary_words", 30):
            f.append(Finding(WARN, "V07 description", f"description is {words} words", d.id))
        if words < 4:
            f.append(Finding(WARN, "V07 description", "description is too short to be useful", d.id))
        if title and desc.lower().rstrip(".") == title.lower():
            f.append(Finding(WARN, "V07 description", "description repeats the title", d.id))
    if title and len(title.split()) > q.get("max_title_words", 10):
        f.append(Finding(WARN, "V07 title", f"title is {len(title.split())} words", d.id))
    text = f"{title} {desc}"
    source_text = " ".join([it.title, it.body, it.release_note] +
                           [f"{r['title']} {r.get('body', '')}" for r in it.related])
    invented = [n for n in NUM_RE.findall(text) if n not in source_text]
    if invented:
        f.append(Finding(ERROR, "V07 hallucination",
                         f"number(s) not in any source data: {invented}", d.id))
    for term in q.get("banned_terms", []):
        if re.search(rf"\b{re.escape(term)}\b", text, re.I):
            f.append(Finding(WARN, "V07 jargon", f"internal/jargon term '{term}'", d.id))
    if KEY_OR_PATH.search(text):
        f.append(Finding(WARN, "V07 jargon", "ticket key, PR number or file path in text", d.id))
    return f


def check_template(notes: str, tmpl: str, cfg: dict) -> list[Finding]:
    """Structural check of ANY notes document against the template (also used for MCP drafts)."""
    problems, got = template.check(notes, tmpl)
    f = [Finding(lvl, "V10 template", msg) for lvl, msg in problems]
    roots, loops = template.fields(tmpl)
    for r in sorted(roots):
        if r in got and not got[r].strip():
            f.append(Finding(ERROR, "V10 template", f"'{r}' is empty"))
    fmt = cfg.get("template", {}).get("date_format", "%Y-%m-%d")
    if got.get("releaseDate"):
        try:
            dt.datetime.strptime(got["releaseDate"], fmt)
        except ValueError:
            f.append(Finding(ERROR, "V10 template",
                             f"Release Date '{got['releaseDate']}' does not match format {fmt}"))
    for name in loops:
        for e in got.get(name, []):
            if len(e.get("description", "").split()) < 2:
                f.append(Finding(ERROR, "V10 template", f"{name} item '{e.get('title')}' has no real description"))
    return f
