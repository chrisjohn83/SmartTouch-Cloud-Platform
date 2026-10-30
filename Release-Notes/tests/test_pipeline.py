"""Run: python -m pytest -q   (no network, no API key needed)"""
from pathlib import Path

import yaml

from relnotes import llm, template
from relnotes.models import ChangeItem, Decision
from relnotes.normalize import link_and_merge
from relnotes.pipeline import classify, load_fixture
from relnotes.render import build_data, load_template, render
from relnotes.rules import Rules
from relnotes.validate import ERROR, check_template, validate

ROOT = Path(__file__).resolve().parent.parent
CFG = yaml.safe_load((ROOT / "config.yaml").read_text())
TMPL = load_template(CFG, ROOT)
FIX = ROOT / "fixtures"
META = {"version": "4.2.0", "release_date": "2026-10-30", "since": "2026-10-01", "until": "2026-10-30",
        "sources": "x", "generated_at": "now"}


def _candidates():
    raw = sum((load_fixture(n, FIX, CFG["sources"][n]) for n in ("github", "jira", "bitbucket")), [])
    rules = Rules(CFG["rules"])
    excl = rules.apply(raw)
    cands, linked = link_and_merge(raw, excl)
    return raw, rules, {**excl, **linked}, cands


def _run(decisions=None):
    raw, rules, _, cands = _candidates()
    items = {c.id: c for c in cands}
    decisions = decisions if decisions is not None else classify(cands, CFG, offline=True)
    data, omitted = build_data(items, decisions, CFG, META)
    notes = render(TMPL, data)
    return notes, data, validate(items, decisions, rules, CFG, notes, TMPL, data, omitted, len(raw)), items


def test_rules_linking_and_known_issues():
    raw, _, excl, cands = _candidates()
    ids = {c.id for c in cands}
    assert "github:#105" in excl and "bot" in excl["github:#105"].reason
    assert "bitbucket:#48" in excl                       # linked to internal PLAT-230
    assert "jira:PLAT-241" in excl                       # internal known issue
    assert "github:#101" not in ids                      # folded into PLAT-210
    assert {"jira:PLAT-240", "github:issue#77"} <= ids


def test_demo_output_follows_template():
    notes, data, findings, _ = _run()
    assert notes.startswith("Release Notes - Version 4.2.0\nRelease Date: October 30, 2026\n")
    assert not [f for f in findings if f.level == ERROR], findings
    assert len(data["knownIssues"]) == 2 and data["bugFixes"]
    assert all(e["description"] for s in ("newFeatures", "bugFixes", "knownIssues") for e in data[s])
    assert "Search is slow" not in notes                 # symptom text must not be used as description


def test_empty_sections_use_fallback_text():
    data = {"versionNumber": "1.0", "releaseDate": "October 30, 2026", "productName": "X",
            "newFeatures": [], "bugFixes": [], "knownIssues": []}
    out = render(TMPL, data)
    for s in ("No new features introduced in this release.", "No bug fixes in this release.",
              "There are no known issues reported for this release."):
        assert s in out
    assert not check_template(out, TMPL, CFG)


def test_template_checker_catches_deviations():
    notes, *_ = _run()
    bad = (notes.replace("Product: Acme Platform\n", "")
                .replace("Release Date: October 30, 2026", "Release Date: 30/10/2026")
                .replace("\n* Fix memory leak", "\n- Fix memory leak")
                .replace("Known Issues\n", "Known Issues\nNo bug fixes in this release.\n"))
    msgs = " | ".join(f.message for f in check_template(bad, TMPL, CFG) if f.level == ERROR)
    assert "missing required line: 'Product: {productName}'" in msgs
    assert "does not match format" in msgs
    assert "unexpected line" in msgs and "- Fix memory leak" in msgs
    leftover = notes.replace("Acme Platform", "{productName}")
    assert any("unrendered" in f.message for f in check_template(leftover, TMPL, CFG))


def test_validator_catches_bad_model_output():
    _, _, _, cands = _candidates()
    ids = [c.id for c in cands]
    bad = [
        Decision(ids[0], False, "Shiny Stuff", "x", "Something new for users.", "A", 0.9),
        Decision(ids[1], False, "Enhancements", "x", "Search is now 80% faster for everyone.", "Search", 0.9),
        Decision("github:#999", False, "Bug Fixes", "x", "Fixed it for all users.", "B", 0.9),
        Decision(ids[3], False, "Enhancements", "x", "", "No description", 0.3),
        Decision("jira:PLAT-240", False, "Bug Fixes", "x", "Imports work now in all cases.", "Import", 0.9),
    ]
    _, _, findings, _ = _run(bad)
    checks = {f.check for f in findings}
    assert {"V01 coverage", "V02 category", "V07 hallucination", "V07 description", "V06 confidence"} <= checks


def test_known_issue_also_fixed_is_error():
    raw, rules, _, cands = _candidates()
    decisions = classify(cands, CFG, offline=True)
    items = {c.id: c for c in cands}
    items["jira:PLAT-240"].jira_keys = ["PLAT-220"]      # same key as a fixed bug
    data, omitted = build_data(items, decisions, CFG, META)
    f = validate(items, decisions, rules, CFG, render(TMPL, data), TMPL, data, omitted, len(raw))
    assert any(x.check == "V13 known vs fixed" for x in f)


def test_template_fields_and_prompt():
    roots, loops = template.fields(TMPL)
    assert roots == {"versionNumber", "releaseDate", "productName"}
    assert loops == {k: {"title", "description"} for k in ("newFeatures", "bugFixes", "knownIssues")}
    _, _, _, cands = _candidates()
    p = llm.build_prompt(cands, CFG)
    assert "Known Issues" in p and '"description"' in p and "Never invent numbers" in p
    assert llm.parse_json('```json\n{"decisions":[{"id":"a"}]}\n```')["decisions"][0]["id"] == "a"
