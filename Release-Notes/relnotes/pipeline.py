"""Orchestration: intake → rules → link → classify → template data → render → validate."""
from __future__ import annotations

import datetime as dt
import json
from collections import Counter
from pathlib import Path

from . import heuristic, llm
from .models import ChangeItem, Decision
from .normalize import link_and_merge
from .render import KNOWN, build_data, load_template, render
from .rules import Rules
from .sources import ADAPTERS
from .sources import bitbucket as bb, github as gh, jira as jr
from .validate import ERROR, WARN, Finding, validate

ROOT = Path(__file__).resolve().parent.parent


def collect(cfg: dict, since: str, until: str, version: str, demo_dir: Path | None) -> list[ChangeItem]:
    items: list[ChangeItem] = []
    for name, scfg in cfg.get("sources", {}).items():
        if not scfg.get("enabled", True):
            continue
        if demo_dir:
            items += load_fixture(name, demo_dir, scfg)
            continue
        mod = ADAPTERS[name]
        items += mod.fetch(scfg, since, until)
        if hasattr(mod, "fetch_known_issues"):
            items += mod.fetch_known_issues(scfg, version)
    return items


def load_fixture(name: str, d: Path, scfg: dict) -> list[ChangeItem]:
    """Fixtures are raw API payloads, so the real parsers are exercised."""
    raw = json.loads((d / f"{name}.json").read_text())
    if name == "github":
        out = [gh.parse_pr(pr, pr.get("_files", [])) for pr in raw["items"]]
        if scfg.get("known_issue_label"):
            out += [gh.parse_issue(i) for i in raw.get("known_issues", [])]
        return out
    if name == "jira":
        rn = scfg.get("release_note_field")
        out = [jr.parse_issue(i, scfg["base_url"], rn) for i in raw["issues"]]
        if scfg.get("known_issues_jql"):
            out += [jr.parse_issue(i, scfg["base_url"], rn, kind="known_issue")
                    for i in raw.get("known_issues", [])]
        return out
    if name == "bitbucket":
        return [bb.parse_pr(pr, pr.get("_files", [])) for pr in raw["values"]]
    raise ValueError(name)


def classify(candidates: list[ChangeItem], cfg: dict, offline: bool) -> list[Decision]:
    max_words = cfg["quality"].get("max_summary_words", 30)
    if offline:
        out = []
        for it in candidates:
            if it.kind == "known_issue":
                cat, conf, why = KNOWN, 1.0, "known-issue intake"
            else:
                cat, conf, why = heuristic.classify(it)
            title, desc = heuristic.describe(it, cat, max_words)
            out.append(Decision(it.id, False, cat, why, desc, title, conf, decided_by="heuristic"))
        return out
    decisions = llm.classify(candidates, cfg)
    by_id = {c.id: c for c in candidates}
    for d in decisions:
        it = by_id.get(d.id)
        if it is None:
            continue
        if it.kind == "known_issue":        # intake decides this, not the model
            d.category = KNOWN
            continue
        cat, conf, _ = heuristic.classify(it)   # deterministic second opinion
        if conf >= cfg["quality"].get("second_opinion_min_conf", 0.75):
            d.second_opinion = cat
    return decisions


def describe_sources(cfg: dict) -> str:
    parts = []
    for name, s in cfg.get("sources", {}).items():
        if not s.get("enabled", True):
            continue
        if name == "github":
            parts.append(f"GitHub {s['repo']}")
        elif name == "jira":
            parts.append(f"Jira {s['project']}")
        elif name == "bitbucket":
            parts.append(f"Bitbucket {s['workspace']}/{s['repo']}")
    return ", ".join(parts)


def run(cfg: dict, since: str, until: str, version: str, out_dir: Path,
        offline: bool = False, demo_dir: Path | None = None) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    rules = Rules(cfg["rules"])
    tmpl = load_template(cfg, ROOT)

    raw = collect(cfg, since, until, version, demo_dir)
    rule_excl = rules.apply(raw)
    candidates, linked_excl = link_and_merge(raw, rule_excl)
    excluded = {**rule_excl, **linked_excl}
    decisions = classify(candidates, cfg, offline)

    items = {c.id: c for c in candidates}
    meta = {"version": version, "release_date": until, "since": since, "until": until,
            "sources": describe_sources(cfg),
            "generated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M")}
    data, omitted = build_data(items, decisions, cfg, meta)
    notes = render(tmpl, data)
    findings = validate(items, decisions, rules, cfg, notes, tmpl, data, omitted, len(raw))

    (out_dir / "release_notes.txt").write_text(notes)
    (out_dir / "release_notes.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
    (out_dir / "decisions.json").write_text(json.dumps({
        "items": {i.id: i.to_dict() for i in raw},
        "decisions": [d.to_dict() for d in list(excluded.values()) + decisions],
        "findings": [f.__dict__ for f in findings]}, indent=2, ensure_ascii=False))
    (out_dir / "quality_report.md").write_text(
        report(raw, candidates, excluded, decisions, data, findings, offline, meta, cfg))

    errors = sum(f.level == ERROR for f in findings)
    warns = sum(f.level == WARN for f in findings)
    counts = ", ".join(f"{k} {len(v)}" for k, v in data.items() if isinstance(v, list))
    print(f"{len(raw)} extracted → {len(candidates)} candidates → {counts} | {errors} errors, {warns} warnings")
    print(f"Wrote {out_dir}/release_notes.txt, release_notes.json, quality_report.md, decisions.json")
    return 1 if errors else 0


def report(raw, candidates, excluded, decisions, data, findings: list[Finding], offline, meta, cfg) -> str:
    errors = [f for f in findings if f.level == ERROR]
    warns = [f for f in findings if f.level == WARN]
    status = "❌ BLOCKED — fix errors before publishing" if errors else (
        "⚠️ PASS WITH REVIEW — check the review queue" if warns else "✅ PASS")
    by_source = Counter(f"{i.source} ({i.kind.replace('_', ' ')})" for i in raw)
    by_cat = Counter(d.category for d in decisions if not d.excluded)
    reasons = Counter(d.reason.split("(")[0].strip() for d in excluded.values())
    sec_map = cfg["template"]["sections"]
    L = [f"# Quality report — Version {meta['version']}", "", f"**Status:** {status}", "",
         f"Template: `{cfg['template']['file']}` · Classifier: "
         f"{'heuristic (offline)' if offline else 'LLM + heuristic second opinion'} · "
         f"Period {meta['since']} to {meta['until']} · generated {meta['generated_at']}", "",
         "## Intake", "", "| Source | Extracted |", "|---|---|"]
    L += [f"| {s} | {n} |" for s, n in sorted(by_source.items())]
    merged = len(raw) - len(candidates) - len(excluded)
    L += [f"| **Total** | **{len(raw)}** |", "",
          f"After rules and cross-source linking: **{len(candidates)}** candidates "
          f"({merged} pull requests folded into their Jira issue).", "",
          "## Exclusions (deterministic rules)", "", "| Rule | Count |", "|---|---|"]
    L += [f"| {r} | {n} |" for r, n in reasons.most_common()]
    L += ["", "## Template sections", "", "| Section | Fed by categories | Items |", "|---|---|---|"]
    for sec, cats in sec_map.items():
        L.append(f"| {sec} | {', '.join(f'{c} ({by_cat.get(c, 0)})' for c in cats)} | {len(data.get(sec, []))} |")
    unmapped = [c for c in by_cat if not any(c in v for v in sec_map.values())]
    if unmapped:
        L.append(f"| _not in template_ | {', '.join(f'{c} ({by_cat[c]})' for c in unmapped)} | omitted |")
    L += ["", f"## Errors ({len(errors)})", ""]
    L += [f"- **{f.check}** `{f.item_id}` — {f.message}" for f in errors] or ["None."]
    L += ["", f"## Review queue ({len(warns)})", ""]
    L += [f"- **{f.check}** `{f.item_id}` — {f.message}" for f in warns] or ["None."]
    L += ["", "## Reviewer checklist", "",
          "- [ ] New Features are user-visible; Bug Fixes describe the fixed behaviour",
          "- [ ] Known Issues are still open and include a workaround where one exists",
          "- [ ] Nothing internal slipped through; nothing user-facing wrongly excluded",
          "- [ ] Every description is accurate to its source and free of invented facts",
          "- [ ] Omitted items (if any) really don't belong in the notes", ""]
    return "\n".join(L)
