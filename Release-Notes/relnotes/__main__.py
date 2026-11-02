"""CLI.

  python -m relnotes generate --since 2026-10-01 --until 2026-10-30 --version 4.2.0
  python -m relnotes generate --demo --offline          # no credentials needed
  python -m relnotes eval [--offline]
  python -m relnotes check-template path/to/notes.txt  # validate any notes file against the template
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from .evaluate import run_eval
from .pipeline import run
from .render import load_template
from .validate import ERROR, check_template

ROOT = Path(__file__).resolve().parent.parent


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="relnotes")
    p.add_argument("--config", default=str(ROOT / "config.yaml"))
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate")
    g.add_argument("--since", default="2026-10-01")
    g.add_argument("--until", default="2026-10-30")
    g.add_argument("--version", default="unreleased")
    g.add_argument("--out", default="out")
    g.add_argument("--offline", action="store_true", help="heuristic classifier, no API call")
    g.add_argument("--demo", action="store_true", help="read sample API payloads from fixtures/")

    e = sub.add_parser("eval")
    e.add_argument("--set", default=str(ROOT / "fixtures" / "eval_set.json"))
    e.add_argument("--offline", action="store_true")

    t = sub.add_parser("check-template")
    t.add_argument("notes")

    a = p.parse_args(argv)
    cfg = yaml.safe_load(Path(a.config).read_text())

    if a.cmd == "generate":
        demo = ROOT / "fixtures" if a.demo else None
        return run(cfg, a.since, a.until, a.version, Path(a.out), a.offline, demo)
    if a.cmd == "eval":
        return run_eval(cfg, Path(a.set), a.offline)
    findings = check_template(Path(a.notes).read_text(), load_template(cfg, ROOT), cfg)
    for f in findings:
        print(f"{f.level} {f.check}: {f.message}")
    print("Template OK" if not findings else f"{len(findings)} problem(s)")
    return 1 if any(f.level == ERROR for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
