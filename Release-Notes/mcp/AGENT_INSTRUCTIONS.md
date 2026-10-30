# Interactive path: drafting release notes in Claude with MCP

Use this when a person wants to draft or adjust notes conversationally. Connect the
GitHub and Atlassian (Jira + Bitbucket) MCP servers/connectors in Claude, then paste
or save these instructions as a project instruction or skill.

---

You draft release notes for **{product} {version}** covering **{since} to {until}**.

1. **Collect** merged PRs from GitHub `{repo}` and Bitbucket `{workspace}/{repo}`, and Jira
   issues in project `{project}` that are Done in the window (or in fixVersion `{version}`).
2. **Exclude**, before categorizing, anything that matches the rules in `config.yaml`
   (`rules:` section): bot authors, WIP/temp, `chore:`/`ci:`/`test:` prefixes, merge and
   revert commits, lockfile/test/CI-only changes, `internal` labels, Sub-tasks. List each
   exclusion with the rule that matched.
3. **Link**: fold any PR whose title, description or branch contains a Jira key into that
   issue. If the issue is excluded, exclude the PR too.
4. **Categorize** with the definitions, examples and decision rules in `config.yaml`
   (`categories:`). New Features and Enhancements both go under **New Features**; Bug Fixes
   under **Bug Fixes**; documentation-only changes are left out. **Known Issues** are open
   Jira/GitHub issues labelled `known-issue` (not internal) — include impact and workaround.
5. **Write** the notes in exactly the standard template (`templates/release_notes.tmpl`).
   Every item is `* Title: Description` — a short title with no colon, then one or two
   sentences. Use the exact empty-section sentence when a section has nothing:

   ```
   Release Notes - Version {version}
   Release Date: October 30, 2026
   Product: {product}
   Purpose
   This document summarizes the key updates in the current software release, including new features, bug fixes, and any known issues. These notes help stakeholders and users understand the improvements and outstanding issues impacting the system.
   New Features
   * Title: Description.
   Bug Fixes
   No bug fixes in this release.
   Known Issues
   * Title: Impact. Workaround: ….
   ```

6. **Never invent facts**: no numbers, customers or capabilities that are not in the source.
7. **Verify** before handing over: save the file and run
   `python -m relnotes check-template release_notes.txt`. Fix every ERROR, and list
   low-confidence or borderline items for the person to review.
