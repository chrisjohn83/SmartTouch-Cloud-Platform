---
persona: [developer]
task: [deployment, remote-access]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-06"
tags: [deployment, verification, remote-access, session-broker, audit, stctl]
sequence: 3
part-of: deploy-first-iot-service
related:
  - docs/developers/get-started/deploy-first-iot-service/02-build-push-image.md
  - docs/developers/get-started/connect-first-device/index.md

ai-retrieval-questions:
  - "How do I verify the Remote Access Service is running?"
  - "How do I check the session broker is active?"
  - "How do I confirm remote access protocols are available?"
  - "How do I verify the remote access audit log is enabled?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Verify the session broker is running

> **Keyword:** How do I verify the Remote Access Service is running?
> **Part of:** [Deploy the Remote Access Service](./index.md) — Step 3 of 3

After your pull request merges, Argo CD deploys the Remote Access Service. This tutorial confirms the broker is healthy, the configured protocols are active, and audit logging is recording sessions.

---

## Goal

Confirm the Remote Access Service is running in `dev`, both enabled protocols are available, and the audit log is operational.

---

## Prerequisites

- Completed [Build and push the Remote Access Service image](./02-build-push-image.md)
- Pull request with SSD and Dockerfile merged to `main`
- At least 2 minutes elapsed since the merge

---

## Steps

### Step 1 — Check deployment status

```bash
stctl status --env dev --service remote-access-service
```

Expected output:

```text
Service:     remote-access-service
Environment: dev
Status:      Running
Replicas:    2/2 ready
Image:       harbor.smarttouch.io/myteam/remote-access-service:1.0.0
Deployed:    3 minutes ago by github-actions
```

### Step 2 — Verify the session broker status

```bash
stctl remote-access status --env dev
```

Expected output:

```text
Remote Access Service:  available
Session broker:         ready
Protocols:
  shell          enabled    roles: platform-engineer, administrator
  diagnostics    enabled    roles: platform-engineer, administrator, developer
  file-transfer  disabled
Session limits:
  max concurrent:   50
  session timeout:  30m
  idle timeout:     5m
Active sessions:    0
```

All enabled protocols must show `enabled` before devices can be connected for remote access.

### Step 3 — Verify audit logging is active

```bash
stctl remote-access audit status --env dev
```

Expected output:

```text
Audit logging:   enabled
Retention:       90 days
Keystroke log:   disabled
Log destination: smarttouch-audit-stream
Events recorded: 0 (no sessions opened yet)
```

`Events recorded: 0` is expected — no sessions have been opened yet. The important check is that `Audit logging: enabled` and the log destination is reachable.

### Step 4 — Run a probe session

Open a probe session to confirm the broker will accept connections. The probe uses a system test device and closes immediately — it is safe to run in any environment.

```bash
stctl remote-access probe --env dev
```

Expected output:

```text
✔  Probe session opened successfully
Protocol:      diagnostics
Device:        smarttouch-probe-device (system test device)
Duration:      1s
Session ID:    sess-probe-001
Broker:        responded within 120ms
✔  Probe session closed
✔  Audit event recorded: sess-probe-001
```

The final line — `✔  Audit event recorded` — confirms the audit log captured the probe session end-to-end.

---

## Validation

The Remote Access Service is fully operational when all four checks pass:

| Check | Command | Expected |
| --- | --- | --- |
| Service running | `stctl status --env dev --service remote-access-service` | `Running, 2/2 ready` |
| Broker ready | `stctl remote-access status --env dev` | `Session broker: ready` |
| Protocols active | Same command | `shell: enabled, diagnostics: enabled` |
| Audit operational | `stctl remote-access probe --env dev` | `✔  Audit event recorded` |

---

## Troubleshooting

**`Session broker: starting`** after 5 minutes
The broker is waiting for its TLS certificates from Vault. Check:

```bash
stctl logs --env dev --service remote-access-service --since 5m | grep vault
```

If you see `permission denied`, the service's Vault policy does not include the remote access TLS path. Ask your Administrator to apply the `remote-access-service` Vault policy.

**`stctl remote-access probe` fails with `no probe device available`**
The SmartTouch probe device is not registered in your `dev` environment. Contact your Administrator to register it.

**Audit logging shows `log destination: unreachable`**
The audit stream endpoint is not reachable from the cluster. Check network policies: the Remote Access Service needs egress access to the `smarttouch-audit` service on port 4317.

---

## Next steps

The Remote Access Service is deployed and ready to broker sessions.

- [Connect a device for remote access](../connect-first-device/index.md)
- [How do I view the session audit log?](../../observability/how-to-view-logs.md)
