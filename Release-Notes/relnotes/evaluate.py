"""Accuracy evaluation against a labeled test set (20–30 changes with known answers).

Measures the whole decision path (rules + classifier), as the docs recommend:
accuracy, false positives (should be excluded but published), false negatives
(user-facing but excluded), and a confusion matrix. Fails below the threshold.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .models import EXCLUDED, ChangeItem
from .pipeline import classify
from .rules import Rules


def run_eval(cfg: dict, path: Path, offline: bool) -> int:
    data = json.loads(path.read_text())
    items = [ChangeItem.from_dict(d["item"]) for d in data]
    expected = {d["item"]["id"]: d["expected"] for d in data}
    rules = Rules(cfg["rules"])
    excl = rules.apply(items)
    cands = [i for i in items if i.id not in excl]
    predicted = {i: EXCLUDED for i in excl}
    for d in classify(cands, cfg, offline):
        predicted[d.id] = EXCLUDED if d.excluded else d.category

    total = len(items)
    correct = sum(predicted.get(i) == e for i, e in expected.items())
    fp = sum(e == EXCLUDED and predicted.get(i) != EXCLUDED for i, e in expected.items())
    fn = sum(e != EXCLUDED and predicted.get(i) == EXCLUDED for i, e in expected.items())
    acc = correct / total
    conf = Counter((expected[i], predicted.get(i, "MISSING")) for i in expected)
    labels = [c["name"] for c in cfg["categories"]] + [EXCLUDED]

    print(f"Eval set: {total} changes  ({'heuristic' if offline else 'LLM'})")
    print(f"Accuracy {acc:.0%} | false positives {fp / total:.0%} | false negatives {fn / total:.0%}")
    print("\nConfusion (rows = expected, cols = predicted):")
    short = [l[:9] for l in labels]
    print(" " * 16 + " ".join(f"{s:>9}" for s in short))
    for e in labels:
        print(f"{e[:15]:<16}" + " ".join(f"{conf[(e, p)]:>9}" for p in labels))
    misses = [(i, expected[i], predicted.get(i)) for i in expected if predicted.get(i) != expected[i]]
    if misses:
        print("\nMisses:")
        for i, e, p in misses:
            print(f"  {i}: expected {e}, got {p}  — {next(x.title for x in items if x.id == i)}")
    gate = cfg["quality"].get("min_eval_accuracy", 0.85)
    print(f"\nGate {gate:.0%}: {'PASS' if acc >= gate else 'FAIL'}")
    return 0 if acc >= gate else 1
