# Quality report — Version 4.2.0

**Status:** ⚠️ PASS WITH REVIEW — check the review queue

Template: `templates/release_notes.tmpl` · Classifier: heuristic (offline) · Period 2026-10-01 to 2026-10-30 · generated 2026-10-30 16:08

## Intake

| Source | Extracted |
|---|---|
| bitbucket (change) | 8 |
| github (change) | 14 |
| github (known issue) | 1 |
| jira (change) | 8 |
| jira (known issue) | 2 |
| **Total** | **33** |

After rules and cross-source linking: **16** candidates (4 pull requests folded into their Jira issue).

## Exclusions (deterministic rules)

| Rule | Count |
|---|---|
| only internal/test/lockfile paths changed | 2 |
| prefix 'chore:' | 1 |
| bot author | 1 |
| keyword 'wip' | 1 |
| prefix 'ci:' | 1 |
| prefix 'merge branch' | 1 |
| label 'internal' | 1 |
| issue type 'Sub-task' | 1 |
| keyword 'internal' | 1 |
| prefix 'revert' | 1 |
| keyword 'temp' | 1 |
| linked to excluded PLAT-230 | 1 |

## Template sections

| Section | Fed by categories | Items |
|---|---|---|
| newFeatures | New Features (4), Enhancements (4) | 8 |
| bugFixes | Bug Fixes (4) | 4 |
| knownIssues | Known Issues (2) | 2 |
| _not in template_ | Documentation (2) | omitted |

## Errors (0)

None.

## Review queue (4)

- **V07 jargon** `github:#109` — internal/jargon term 'refactor'
- **V07 jargon** `github:issue#77` — internal/jargon term 'endpoint'
- **V14 omitted** `github:#108` — 'Documentation' has no section in the template — not published
- **V14 omitted** `bitbucket:#45` — 'Documentation' has no section in the template — not published

## Reviewer checklist

- [ ] New Features are user-visible; Bug Fixes describe the fixed behaviour
- [ ] Known Issues are still open and include a workaround where one exists
- [ ] Nothing internal slipped through; nothing user-facing wrongly excluded
- [ ] Every description is accurate to its source and free of invented facts
- [ ] Omitted items (if any) really don't belong in the notes
