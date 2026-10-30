"""LLM categorization using the v4 production prompt, adapted for structured output.

The model returns JSON decisions (one per change id) instead of markdown, so
every claim it makes can be validated before anything is rendered.
"""
from __future__ import annotations

import json
import re

from .models import ChangeItem, Decision

PROMPT = """You are helping categorize software changes for customer-facing release notes.

Each change below was collected from GitHub, Jira or Bitbucket. Jira issues may include the
titles and descriptions of their linked pull requests. Deterministic rules have ALREADY removed bot commits,
WIP/temp work, merge/revert commits, chore/ci/build/test/style prefixes, lockfile-only and
test-only changes. Categorize what remains.

## Categories
{categories}

## Decision rules
When signals conflict, ask in this order:
1. Can users now do something they could not do at all before? → {c0}
2. Does it improve or change something that already exists? → {c1}
3. Does it correct behaviour that was not working as intended? → {c2}
4. Is it only documentation? → {c3}
When unsure between {c0} and {c1}, choose {c1}.
A Jira issue type is strong evidence (Bug usually means {c2}) but not proof.
If a Jira "release_note_field" is present, treat it as the author's intended wording.

## Additional exclusions
Set "excluded": true (with a reason) only when the change has no effect a user or API
consumer could notice: internal tooling, build or infrastructure work, formatting-only,
comment-only, or anything marked internal. Do not exclude user-visible changes.

## Known issues
Items with "kind": "known_issue" are open problems that ship with this release. Do not
categorize them: set "category": "Known Issues". Describe the user impact and, if the
data contains one, the workaround. Never promise a fix date.

## Title and description (both required — they fill "* {{title}}: {{description}}")
- "title": a short user-facing name for the change, at most 8 words, no trailing period,
  no ticket numbers (e.g. "Webhook support", "Safari session timeout").
- "description": one or two plain-language sentences, at most {max_words} words, ending
  with a period. Say what users can now do, or what now works correctly — for a bug fix,
  describe the fixed behaviour, not only the symptom. Must not repeat the title.
- Use ONLY facts present in the change data. Never invent numbers, percentages, product
  names, customers or capabilities.
- No ticket numbers, file paths, class names or internal jargon.

## Output
Reply with ONLY a JSON object, no prose and no code fences:
{{"decisions": [{{"id": "<copy verbatim>", "excluded": false, "category": "<one of: {names} | Known Issues>",
"title": "<text>", "description": "<text>", "reason": "<short why>", "confidence": 0.0}}]}}
Return exactly one decision per change id listed below, and no other ids.
"confidence" is your probability (0–1) that the category is correct.

## Changes
{changes}
"""


def render_categories(categories: list[dict]) -> str:
    blocks = []
    for c in categories:
        b = [f"### {c['name']}", f"**Definition:** {c['definition']}"]
        if c.get("examples"):
            b.append("**Examples:**\n" + "\n".join(f'- "{e}"' for e in c["examples"]))
        if c.get("not_examples"):
            b.append("**NOT examples:**\n" + "\n".join(f"- {e}" for e in c["not_examples"]))
        if c.get("keywords"):
            b.append("**Keywords:** " + ", ".join(f'"{k}"' for k in c["keywords"])
                     + " (signals only — the definition wins)")
        blocks.append("\n".join(b))
    return "\n\n".join(blocks)


def build_prompt(items: list[ChangeItem], cfg: dict) -> str:
    cats = cfg["categories"]
    names = [c["name"] for c in cats]
    pad = names + [names[-1]] * (4 - len(names))
    return PROMPT.format(
        categories=render_categories(cats), c0=pad[0], c1=pad[1], c2=pad[2], c3=pad[3],
        names=" | ".join(names), max_words=cfg["quality"].get("max_summary_words", 30),
        changes=json.dumps([i.to_prompt_dict() for i in items], indent=1, ensure_ascii=False),
    )


def parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("no JSON object found")
    data = json.loads(text[start:end + 1])
    if not isinstance(data.get("decisions"), list):
        raise ValueError("'decisions' list missing")
    return data


def classify(items: list[ChangeItem], cfg: dict) -> list[Decision]:
    import anthropic  # imported lazily so --offline needs no SDK

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    llm = cfg.get("llm", {})
    size = int(llm.get("batch_size", 40))
    out: list[Decision] = []
    for i in range(0, len(items), size):
        batch = items[i:i + size]
        messages = [{"role": "user", "content": build_prompt(batch, cfg)}]
        data = None
        for _ in range(2):
            resp = client.messages.create(model=llm.get("model", "claude-sonnet-5-5"),
                                          max_tokens=int(llm.get("max_tokens", 8000)),
                                          messages=messages)
            text = "".join(b.text for b in resp.content if b.type == "text")
            try:
                data = parse_json(text)
                break
            except (ValueError, json.JSONDecodeError) as e:
                messages += [{"role": "assistant", "content": text},
                             {"role": "user", "content": f"That was not valid JSON ({e}). "
                                                         "Reply with only the JSON object."}]
        if data is None:
            raise RuntimeError("Model did not return valid JSON after a retry")
        for d in data["decisions"]:
            out.append(Decision(
                id=str(d.get("id", "")), excluded=bool(d.get("excluded", False)),
                category=d.get("category"), reason=d.get("reason", ""),
                title=(d.get("title") or "").strip(),
                description=(d.get("description") or "").strip(),
                confidence=float(d.get("confidence", 0.5)), decided_by="llm"))
    return out
