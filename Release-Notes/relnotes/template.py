"""Renderer and structural checker for the standard template.

The template uses docxtemplater-style tags, so the same file works for a Word
template filled by docxtemplater and for the text rendering here:
  {var}            value
  {#list}...{/list} repeat for each item (item fields first, then root fields)
  {^list}...{/list} only when the list is empty
"""
from __future__ import annotations

import re

TAG = re.compile(r"\{([#^/]?)(\w+)\}")
STANDALONE = re.compile(r"^[ \t]*(\{[#/]\w+\})[ \t]*\n", re.M)


class TemplateError(ValueError):
    pass


def parse(src: str) -> list:
    root: list = []
    stack: list = [("root", None, root)]
    pos = 0
    for m in TAG.finditer(src):
        if m.start() > pos:
            stack[-1][2].append(("text", src[pos:m.start()]))
        kind, name = m.group(1), m.group(2)
        if kind in ("#", "^"):
            node = (kind, name, [])
            stack[-1][2].append(node)
            stack.append(node)
        elif kind == "/":
            if stack[-1][1] != name:
                raise TemplateError(f"closing {{/{name}}} does not match {{{stack[-1][0]}{stack[-1][1]}}}")
            stack.pop()
        else:
            stack[-1][2].append(("var", name))
        pos = m.end()
    if len(stack) != 1:
        raise TemplateError(f"unclosed section {{{stack[-1][0]}{stack[-1][1]}}}")
    if pos < len(src):
        root.append(("text", src[pos:]))
    return root


def fields(src: str) -> tuple[set[str], dict[str, set[str]]]:
    """Root variables and, per loop, the fields its items need."""
    roots: set[str] = set()
    loops: dict[str, set[str]] = {}

    def walk(nodes, loop):
        for n in nodes:
            if n[0] == "var":
                (loops[loop] if loop else roots).add(n[1])
            elif n[0] == "#":
                loops.setdefault(n[1], set())
                walk(n[2], n[1])
            elif n[0] == "^":
                walk(n[2], loop)
    walk(parse(src), None)
    return roots, loops


def _clean(v) -> str:
    return re.sub(r"\s+", " ", str(v if v is not None else "")).strip()


def render(src: str, data: dict) -> str:
    tree = parse(STANDALONE.sub(r"\1", src))  # keep tag, drop its line break

    def go(nodes, scopes) -> str:
        out = []
        for n in nodes:
            if n[0] == "text":
                out.append(n[1])
            elif n[0] == "var":
                val = next((s[n[1]] for s in scopes if isinstance(s, dict) and n[1] in s), "")
                out.append(_clean(val))
            else:
                val = next((s[n[1]] for s in scopes if isinstance(s, dict) and n[1] in s), None)
                if n[0] == "#":
                    if isinstance(val, list):
                        out += [go(n[2], [item] + scopes) for item in val]
                    elif val:
                        out.append(go(n[2], scopes))
                elif not val:
                    out.append(go(n[2], scopes))
        return "".join(out)

    text = go(tree, [data])
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


# ---------- structural check of any rendered document against the template ----------

def _line_regex(line: str) -> tuple[re.Pattern, list[str]]:
    parts, names, pos = [], [], 0
    for m in TAG.finditer(line):
        parts.append(re.escape(line[pos:m.start()]))
        parts.append("(.+?)")
        names.append(m.group(2))
        pos = m.end()
    parts.append(re.escape(line[pos:]))
    return re.compile("".join(parts)), names


def expectations(src: str) -> list[dict]:
    lines = [l.strip() for l in src.splitlines() if l.strip()]
    exp: list[dict] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.fullmatch(r"\{#(\w+)\}", line)
        if m:
            name, body = m.group(1), []
            i += 1
            while i < len(lines) and lines[i] != f"{{/{name}}}":
                body.append(lines[i])
                i += 1
            exp.append({"type": "list", "name": name, "body": [_line_regex(b) for b in body],
                        "raw": body, "fallback": None})
        else:
            m = re.fullmatch(r"\{\^(\w+)\}(.*)\{/\1\}", line)
            prev = next((e for e in reversed(exp) if e["type"] == "list" and m and e["name"] == m.group(1)), None)
            if m and prev:
                prev["fallback"] = m.group(2)
            else:
                rx, names = _line_regex(line)
                exp.append({"type": "line", "rx": rx, "names": names, "raw": line})
        i += 1
    return exp


def check(doc: str, src: str) -> tuple[list[tuple[str, str]], dict]:
    """Return (problems, extracted) where problems are (level, message)."""
    problems: list[tuple[str, str]] = []
    extracted: dict = {}
    left = TAG.findall(doc)
    if left:
        problems.append(("ERROR", f"unrendered placeholder(s): {['{' + a + b + '}' for a, b in left][:5]}"))
    lines = [l.strip() for l in doc.splitlines() if l.strip()]
    i = 0
    for e in expectations(src):
        if e["type"] == "line":
            j = next((k for k in range(i, len(lines)) if e["rx"].fullmatch(lines[k])), None)
            if j is None:
                problems.append(("ERROR", f"missing required line: '{e['raw']}'"))
                continue
            for k in range(i, j):
                problems.append(("ERROR", f"unexpected line before '{e['raw']}': '{lines[k][:70]}'"))
            m = e["rx"].fullmatch(lines[j])
            extracted.update(zip(e["names"], (g.strip() for g in m.groups())))
            i = j + 1
        else:
            items = []
            n = len(e["body"])
            while i + n <= len(lines):
                ms = [rx.fullmatch(lines[i + k]) for k, (rx, _) in enumerate(e["body"])]
                if not all(ms):
                    break
                item = {}
                for (rx, names), m in zip(e["body"], ms):
                    item.update(zip(names, (g.strip() for g in m.groups())))
                items.append(item)
                i += n
            extracted[e["name"]] = items
            has_fallback = i < len(lines) and e["fallback"] is not None and lines[i] == e["fallback"]
            if has_fallback:
                i += 1
            if not items and not has_fallback and e["fallback"] is not None:
                problems.append(("ERROR", f"'{e['name']}' has no items and no fallback text "
                                          f"('{e['fallback']}')"))
            if items and has_fallback:
                problems.append(("ERROR", f"'{e['name']}' has items and also the empty-section text"))
    for k in range(i, len(lines)):
        problems.append(("ERROR", f"unexpected trailing line: '{lines[k][:70]}'"))
    return problems, extracted
