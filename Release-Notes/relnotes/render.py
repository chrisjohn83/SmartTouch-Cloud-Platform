"""Build the template data and render the standard template.

Classification categories are mapped onto template sections by
config `template.sections` (e.g. Enhancements → newFeatures). Categories that
map to no section are omitted and listed in the quality report.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from . import template
from .heuristic import clean_title
from .models import ChangeItem, Decision

KNOWN = "Known Issues"


def load_template(cfg: dict, root: Path) -> str:
    return (root / cfg["template"]["file"]).read_text()


def _sentence(text: str) -> str:
    t = re.sub(r"\s+", " ", text or "").strip()
    return t if not t or t.endswith((".", "!", "?")) else t + "."


def format_date(iso: str, fmt: str) -> str:
    return dt.date.fromisoformat(iso[:10]).strftime(fmt)


def build_data(items: dict[str, ChangeItem], decisions: list[Decision], cfg: dict,
               meta: dict) -> tuple[dict, list[str]]:
    tcfg = cfg["template"]
    sections: dict[str, list[str]] = tcfg["sections"]
    cat_to_sec = {c: s for s, cats in sections.items() for c in cats}
    order = {c: n for n, c in enumerate(c for cats in sections.values() for c in cats)}

    data: dict = {"versionNumber": meta["version"],
                  "releaseDate": format_date(meta["release_date"], tcfg.get("date_format", "%Y-%m-%d")),
                  "productName": cfg.get("product", "")}
    for s in sections:
        data[s] = []
    omitted: list[str] = []
    kept = [d for d in decisions if not d.excluded and d.id in items]
    for d in sorted(kept, key=lambda d: order.get(d.category, 99)):
        it = items[d.id]
        sec = cat_to_sec.get(d.category)
        if not sec:
            omitted.append(d.id)
            continue
        data[sec].append({
            # ':' would make "{title}: {description}" ambiguous
            "title": re.sub(r"\s+", " ", d.title or clean_title(it.title)).replace(":", " -").strip().rstrip("."),
            "description": _sentence(d.description),
            # extra fields: ignored by the template, kept for traceability
            "category": d.category,
            "sources": [{"ref": it.ref, "url": it.url}] +
                       [{"ref": r["id"].split(":", 1)[1], "url": r.get("url", "")} for r in it.related],
        })
    return data, omitted


def render(src: str, data: dict) -> str:
    return template.render(src, data)
