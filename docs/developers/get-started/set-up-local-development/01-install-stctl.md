---
persona: [developer]
task: [local-development, remote-access]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-06"
tags: [stctl, cli, install, remote-access, session, audit, setup]
sequence: 1
part-of: set-up-local-development
related:
  - docs/developers/get-started/set-up-local-development/index.md
  - docs/developers/get-started/set-up-local-development/02-configure-kubernetes.md

ai-retrieval-questions:
  - "How do I install the SmartTouch CLI?"
  - "How do I install stctl?"
  - "How do I use stctl remote-access commands?"
  - "How do I open a remote session from the terminal?"
  - "How do I view remote access audit logs with stctl?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Install the SmartTouch CLI

> **Keyword:** How do I install the SmartTouch CLI?
> **Part of:** [Set up local development](./index.md) — Step 1 of 3

The SmartTouch CLI (`stctl`) is the primary tool for managing remote device access from your terminal. The `stctl remote-access` command group lets you open sessions, list active sessions, close sessions, view audit logs, and probe the session broker — without opening a browser.

---

## Goal

Install `stctl` and verify that the `remote-access` command group is available with all its subcommands.

---

## Prerequisites

- A SmartTouch account
- Internet access

---

## Steps

### Step 1 — Install stctl

**macOS (Homebrew)**

```bash
brew tap smarttouch/tap && brew install stctl
```

**Linux**

```bash
curl -sSL https://get.smarttouch.io/stctl | bash
```

**Windows (WSL2 only)**

Run the Linux command above inside your WSL2 terminal.

### Step 2 — Verify the installation

```bash
stctl version
```

Expected output:

```text
stctl version 2.4.1 (linux/amd64)
SmartTouch CLI — https://docs.smarttouch.io/cli
```

### Step 3 — Authenticate

```bash
stctl auth login
```

A browser window opens. Log in with your SmartTouch credentials and return to the terminal.

Expected output:

```text
✔  Authenticated as alex@example.com
Token expires: 2026-06-07 (renewable)
```

### Step 4 — Verify the remote-access command group

```bash
stctl remote-access --help
```

Expected output lists every remote access subcommand:

```text
Manage SmartTouch remote device access sessions.

Usage:
  stctl remote-access [command]

Available Commands:
  status          Show session broker availability and active session count
  open            Open a remote access session to a device
  list            List all active sessions (your sessions or all, with --all)
  close           Close an active session by session ID
  probe           Run a connectivity probe against the session broker
  audit           View and export session audit logs
  install-agent   Generate and print Remote Access Agent install instructions for a device
```

### Step 5 — Explore key remote-access commands

Familiarise yourself with the three commands you will use most during development:

**Check broker status:**

```bash
stctl remote-access status --env dev
```

**Open a session** (once a device is connected):

```bash
stctl remote-access open \
  --device <device-id> \
  --protocol diagnostics \
  --env dev
```

**View audit log entries from the last hour:**

```bash
stctl remote-access audit list \
  --since 1h \
  --env dev
```

---

## Validation

```bash
stctl version                    # Returns version string
stctl auth status                # Returns your email and organisation
stctl remote-access --help       # Lists all remote-access subcommands
```

---

## Troubleshooting

**`stctl remote-access` not found**
Your `stctl` is older than version 2.3.0. Upgrade:

```bash
brew upgrade stctl               # macOS
curl -sSL https://get.smarttouch.io/stctl | bash   # Linux
```

**`remote access not enabled for your account`**
Remote access is a licensed feature. Contact your SmartTouch Administrator to enable it.

**`Error: token expired`**
Run `stctl auth refresh` or `stctl auth login` to renew.

---

## Next steps

→ Continue to **Step 2:** [Configure your local Kubernetes context](./02-configure-kubernetes.md)
