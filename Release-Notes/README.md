# AI release notes — multi-source intake with quality gates

Pulls changes from **GitHub**, **Jira** and **Bitbucket** (plus open known issues from Jira
and GitHub), filters them with deterministic rules, categorizes them with Claude using the
v4 production prompt, fills the **standard release notes template**
(`templates/release_notes.tmpl`), and **blocks publishing** if the extracted data or the
generated notes fail quality checks.

```
 GitHub PRs ─┐                 ┌─ rules: bots, WIP/temp, chore:/ci:, lockfiles,
 Jira issues ─┼─► normalize ──► │  test-only paths, internal labels, Sub-tasks      ─► excluded (audited)
 Bitbucket PRs┘   (one model)   └─ link: PRs collapse into their Jira issue
                                         │
                                         ▼
                         Claude (v4 prompt → JSON decisions)
                         + heuristic second opinion
                                         │
                                         ▼
                 fill templates/release_notes.tmpl ─► validate ─► CI gate
                                                   │
   release_notes.txt · release_notes.json · quality_report.md · decisions.json
```

## Rules or MCP?

**Both — but for different jobs. Neither replaces the other.**

| Job | Use | Why |
|---|---|---|
| Fetching data in a scheduled/CI pipeline | **Direct REST adapters** (this repo) | Deterministic, testable, no agent in the loop, cheap, same input every run |
| Fetching data interactively ("draft notes for 4.2 and fix the Safari item") | **MCP servers** (GitHub, Atlassian) in Claude | Claude can explore, follow links and answer follow-ups; great for ad-hoc work |
| Deciding what to exclude | **Rules (code)** | Exclusions must be auditable and never drift; the docs show comprehensive explicit rules cut false positives by 85% |
| Deciding the category and writing the summary | **LLM** | Semantic judgement ("is this wholly new?") that keyword rules get wrong |
| Verifying the output | **Rules (code)** | A model should not grade its own work; checks must be reproducible in CI |

MCP is a *transport* (how an AI reaches GitHub/Jira/Bitbucket); rules are *policy* (what
counts as a release note and what a valid release note looks like). Recommended setup:
run this pipeline in CI for every release, and use MCP in Claude for interactive drafting —
then run `python -m relnotes check-template` on whatever Claude produced, so both paths go
through the same gate. See `mcp/AGENT_INSTRUCTIONS.md`.

## Quick start

```bash
pip install -r requirements.txt

# 1. Demo — sample API payloads, no credentials, no API key
python -m relnotes generate --demo --offline --version 4.2.0

# 2. Real run
export GITHUB_TOKEN=... JIRA_EMAIL=... JIRA_API_TOKEN=... BITBUCKET_ACCESS_TOKEN=... ANTHROPIC_API_KEY=...
python -m relnotes generate --since 2026-10-01 --until 2026-10-30 --version 4.2.0

# 3. Measure accuracy on your labeled set (do this after every prompt/rule change)
python -m relnotes eval

# 4. Validate any notes file against the template (e.g. one drafted via MCP)
python -m relnotes check-template out/release_notes.txt
```

Exit code is `1` when any ERROR-level check fails, so CI can block the release.

## The template

`templates/release_notes.tmpl` is the standard template, stored verbatim. It uses
docxtemplater-style tags (`{var}`, `{#list}…{/list}`, `{^list}…{/list}` for the empty-section
text), so the same data also fills a Word copy of the template via docxtemplater.

| Template field | Filled from |
|---|---|
| `{versionNumber}` | `--version` |
| `{releaseDate}` | `--until`, written with `template.date_format` (default `October 30, 2026`) |
| `{productName}` | `product` in `config.yaml` |
| `{#newFeatures}` | categories **New Features + Enhancements** |
| `{#bugFixes}` | category **Bug Fixes** |
| `{#knownIssues}` | open issues labelled `known-issue` in Jira (`known_issues_jql`) and GitHub (`known_issue_label`) |
| `{title}: {description}` | short user-facing title + 1–2 sentence description, written by Claude from source data only |

The template has no Documentation section, so documentation-only changes are **not
published**; each one is listed in the quality report (V14) so nothing disappears silently.
Change `template.sections` in `config.yaml` to route categories differently, e.g. drop
`Enhancements` from `newFeatures` or add a section to the template.

Known issues are decided by intake, never by the model: an issue is a known issue because
it is open and labelled, and the model only writes its title and description (impact plus
workaround, never a fix date).

## Outputs

- `out/release_notes.txt` — the notes rendered from the template
- `out/release_notes.json` — the template data (`versionNumber`, `newFeatures[]`, …); feed it to docxtemplater to fill the Word template. Each item also carries its `category` and source links
- `out/quality_report.md` — status, intake counts, exclusions by rule, errors, review queue, reviewer checklist
- `out/decisions.json` — every extracted item and the decision about it (who decided, why, confidence): the audit trail

## Quality checks

| ID | Check | Level |
|---|---|---|
| V01 | Every candidate decided exactly once; no invented ids | Error |
| V02 | Category is valid; only known-issue intake can produce Known Issues | Error |
| V03 | Nothing published matches an exclusion rule (leakage) | Error |
| V04 | Jira issue type agrees with category (Bug → Bug Fixes) | Warning |
| V05 | Model disagrees with confident rule-based classifier | Warning |
| V06 | Model confidence below threshold | Warning |
| V07 | Description missing (template needs `{title}: {description}`) | Error |
| V07 | Title/description contain numbers not in source data (hallucination) | Error |
| V07 | Too long/short, repeats title, jargon, ticket keys, PR numbers or file paths | Warning |
| V08 | Every entry links to its source | Error |
| V09 | Duplicate entries | Warning |
| V10 | Template conformance, derived from the template file: every fixed line present and in order, header fields filled, date format, `* Title: Description` bullets, empty sections use the exact fallback text, no leftover `{tags}`, nothing extra | Error |
| V11 | Volume sanity: nothing included, or unusually high exclusion rate | Warning |
| V12 | Model excluded a user-facing candidate (possible false negative) | Warning |
| V13 | Same issue listed as both a known issue and a bug fix | Error |
| V14 | Change category has no section in the template, so it was not published | Warning |

## Tuning (the iteration loop from the docs)

1. Replace `fixtures/eval_set.json` with 20–30 **real** changes from your repos, labeled by hand.
2. Run `python -m relnotes eval`, read the misses.
3. Add counter-examples to `categories` in `config.yaml`, or a rule to `rules`.
4. Re-run on the same set. Stop when gains are under 3 points (~90% is the sweet spot).

The bundled eval set was written together with the offline classifier, so its 100% score
only proves the plumbing works — your own labeled set is what measures real accuracy.

If you change the template, the renderer and the V10 check follow automatically (they read
the template file); update `template.sections` so each loop is fed by the right categories.

## Source notes

- **GitHub**: merged PRs via search (max 1,000 per window). Enterprise: set `api_url`.
- **Jira Cloud**: `POST /rest/api/3/search/jql` with token pagination. Prefer `fix_version`
  when you version releases in Jira. A "Release Note" custom field is used as curated wording.
- **Bitbucket Cloud**: merged PRs filtered by `updated_on` (Bitbucket has no merged-date
  filter); Data Center needs a separate adapter for `/rest/api/1.0`.
- **Known issues**: Jira `known_issues_jql` (default: not Done + label `known-issue`) and
  open GitHub issues with `known_issue_label`. Internal-labelled ones are still excluded.
- Linking: a PR whose title, description or branch has a Jira key is folded into that issue.
  If the issue is excluded (e.g. `internal`), its PRs are excluded too.

## Layout

```
relnotes/
  sources/      github.py · jira.py · bitbucket.py · http.py (retry/backoff)
  models.py     ChangeItem, Decision
  rules.py      deterministic exclusions
  normalize.py  cross-source linking
  heuristic.py  offline classifier + second opinion
  llm.py        v4 prompt → JSON decisions
  template.py   template renderer + structural checker
  render.py     decisions → template data
  validate.py   quality checks
  evaluate.py   accuracy / FP / FN / confusion matrix
  pipeline.py   orchestration + quality report
templates/      release_notes.tmpl (the standard template)
config.yaml     sources, template mapping, categories, rules, thresholds
fixtures/       sample raw API payloads + labeled eval set
examples/       output from the demo run
mcp/            instructions for the interactive (MCP) path
.github/workflows/release-notes.yml
```
