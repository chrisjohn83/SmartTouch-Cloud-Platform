---
persona: [developer]
task: [deployment, remote-access]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-06"
tags: [ssd, remote-access, session-broker, audit-logging, role-gating, yaml]
sequence: 1
part-of: deploy-first-iot-service
related:
  - docs/developers/get-started/deploy-first-iot-service/index.md
  - docs/developers/get-started/deploy-first-iot-service/02-build-push-image.md

ai-retrieval-questions:
  - "How do I create an SSD for the Remote Access Service?"
  - "How do I configure session protocols in the SSD?"
  - "How do I enable audit logging for remote access?"
  - "How do I role-gate remote access sessions in SmartTouch?"
  - "What SSD fields control remote device access?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Create the Remote Access Service SSD

> **Keyword:** How do I create an SSD for the Remote Access Service?
> **Part of:** [Deploy the Remote Access Service](./index.md) — Step 1 of 3

The Remote Access Service SSD configures which session protocols are available, which roles can open sessions, how long sessions can remain open, and how the audit log is retained. This tutorial walks through each field with an explanation of the security and operational trade-offs.

---

## Goal

Create and validate a Remote Access Service SSD that enables shell and diagnostics sessions with a 30-minute timeout and 90-day audit retention.

---

## Prerequisites

- `stctl` installed and authenticated
- A code repository for your Remote Access Service

---

## Steps

### Step 1 — Create the SSD file

```bash
touch smarttouch.yaml
```

### Step 2 — Add the core service fields

```yaml
# smarttouch.yaml
# Service Spec Definition — Remote Access Service

service:
  name: remote-access-service
  version: "1.0.0"

deployment:
  replicas: 2
  image: harbor.smarttouch.io/myteam/remote-access-service:1.0.0
  port: 8080
  resources:
    cpu: "250m"
    memory: "256Mi"

observability:
  metrics: true
  tracing: true
```

### Step 3 — Configure the remote access broker

```yaml
remote-access:
  enabled: true
  session-timeout: "30m"           # Maximum duration of any single session.
                                   # Sessions that exceed this are closed automatically.
  max-concurrent-sessions: 50      # Platform-wide limit across all devices.
  idle-timeout: "5m"               # Sessions with no activity for this period are closed.
```

`session-timeout` and `idle-timeout` work independently. A session is closed when either limit is reached first — the shorter of the two always wins. Setting `idle-timeout` shorter than `session-timeout` protects against forgotten open sessions.

### Step 4 — Configure session protocols

```yaml
  protocols:
    - name: shell
      enabled: true
      description: "Interactive terminal session on the device"
    - name: diagnostics
      enabled: true
      description: "Read-only stream of system metrics, logs, and hardware state"
    - name: file-transfer
      enabled: false               # Enable when your devices need secure file upload/download
      description: "Secure file upload and download via SCP-over-WebSocket"
```

Enable only the protocols your use case requires. Each enabled protocol is an additional attack surface — disable `shell` in environments where only read access is needed.

### Step 5 — Configure role-based access

```yaml
  access-control:
    shell:
      allowed-roles:
        - platform-engineer        # Can open interactive shell sessions
        - administrator            # Can open interactive shell sessions
    diagnostics:
      allowed-roles:
        - platform-engineer
        - administrator
        - developer                # Read-only access; safe to grant broadly
    file-transfer:
      allowed-roles:
        - administrator            # Restricted: file transfer carries exfiltration risk
```

Role assignments are evaluated at session-open time. A user whose role changes while a session is active is not disconnected — the check applies only when opening a new session.

### Step 6 — Configure audit logging

```yaml
  audit:
    enabled: true
    retention: "90d"               # How long session records are kept.
                                   # Minimum recommended: 30d. Compliance often requires 90d+.
    log-keystrokes: false          # true = records every keystroke in shell sessions.
                                   # false = records session metadata only (open/close/duration).
                                   # Enable only if required by your compliance policy —
                                   # keystroke logs are sensitive and voluminous.
    alert-on-session-open: false   # true = sends a Slack/webhook notification on every session open.
```

`log-keystrokes: false` is the recommended default. Keystroke logging captures everything typed in a shell session and must be protected as sensitive data. Enable it only under a documented compliance requirement.

### Step 7 — Complete SSD

```yaml
service:
  name: remote-access-service
  version: "1.0.0"

deployment:
  replicas: 2
  image: harbor.smarttouch.io/myteam/remote-access-service:1.0.0
  port: 8080
  resources:
    cpu: "250m"
    memory: "256Mi"

observability:
  metrics: true
  tracing: true

remote-access:
  enabled: true
  session-timeout: "30m"
  max-concurrent-sessions: 50
  idle-timeout: "5m"
  protocols:
    - name: shell
      enabled: true
    - name: diagnostics
      enabled: true
    - name: file-transfer
      enabled: false
  access-control:
    shell:
      allowed-roles: [platform-engineer, administrator]
    diagnostics:
      allowed-roles: [platform-engineer, administrator, developer]
    file-transfer:
      allowed-roles: [administrator]
  audit:
    enabled: true
    retention: "90d"
    log-keystrokes: false
    alert-on-session-open: false
```

### Step 8 — Validate

```bash
stctl validate --file smarttouch.yaml
```

Expected output:

```text
✔  service.name                      valid
✔  deployment.image                  reachable
✔  remote-access.enabled             feature available
✔  remote-access.protocols           shell, diagnostics configured
✔  remote-access.access-control      roles valid
✔  remote-access.audit.retention     90d within plan limit
✔  SSD is valid
```

### Step 9 — Commit

```bash
git add smarttouch.yaml
git commit -m "feat: add Remote Access Service SSD"
git push origin feature/remote-access-service
```

---

## Validation

```bash
stctl validate --file smarttouch.yaml
# Final line must read: ✔  SSD is valid
```

---

## Troubleshooting

**`remote-access.enabled: feature not available`**
Remote access is not enabled for your organisation. Contact your SmartTouch Administrator.

**`remote-access.audit.retention: exceeds plan limit`**
Your plan has a maximum audit retention period. Reduce `retention` to the allowed maximum — check with your Administrator for your plan's limit.

**`remote-access.access-control: unknown role 'developer' for protocol shell`**
The `developer` role cannot be granted shell access by platform policy. Remove it from `shell.allowed-roles`. Developers can be granted `diagnostics` access.

---

## Next steps

→ Continue to **Step 2:** [Build and push the Remote Access Service image](./02-build-push-image.md)
