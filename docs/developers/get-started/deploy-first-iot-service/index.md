---
persona: [developer]
task: [deployment, remote-access]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-06"
tags: [deployment, remote-access, session-broker, audit, ssd, container]
related:
  - docs/developers/get-started/connect-first-device/index.md
  - docs/developers/get-started/set-up-local-development/index.md

ai-retrieval-questions:
  - "How do I deploy the SmartTouch Remote Access Service?"
  - "How do I enable remote device access on SmartTouch?"
  - "What service do I deploy to get remote access to IoT devices?"
  - "How do I set up the remote access session broker?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Deploy the Remote Access Service

> **Keyword:** How do I deploy the SmartTouch Remote Access Service?

This tutorial group walks you through deploying the **Remote Access Service** — the SmartTouch component that brokers secure sessions between your team and IoT devices in the field. By the end, your `dev` environment will have a running Remote Access Service that can accept authenticated shell and diagnostics sessions to any connected device.

---

## What you will learn

- How to write a Service Spec Definition (SSD) that configures the remote access session broker, protocol support, and audit logging
- How to build and push the Remote Access Service container image
- How to verify the broker is active and ready to accept sessions

---

## Key concepts

**Remote Access Session** — a secure, authenticated tunnel from the SmartTouch platform to a specific device. Sessions are scoped to a protocol (shell or diagnostics), role-gated, and have a configurable timeout.

**Remote Access Agent** — a lightweight daemon running on each device. It dials outbound to the Remote Access Service, so sessions work through NAT and firewalls without any port forwarding on the device network.

**Session protocol** — determines what the session tunnel carries. `shell` gives an interactive terminal. `diagnostics` streams read-only system metrics and logs. `file-transfer` allows secure upload and download of files.

**Session audit log** — a tamper-evident record of every session: who opened it, when, how long it lasted, and which device it connected to. Audit logs are retained for a configurable period and are queryable via `stctl`.

---

## Tutorial sequence

| Step | Tutorial | Time |
| --- | --- | --- |
| 1 | [Create the Remote Access Service SSD](./01-create-service-spec.md) | ~10 min |
| 2 | [Build and push the Remote Access Service image](./02-build-push-image.md) | ~15 min |
| 3 | [Verify the session broker is running](./03-verify-deployment.md) | ~5 min |

**Total time:** ~30 minutes

---

## Prerequisites

- `stctl` installed and authenticated — see [Install the SmartTouch CLI](../set-up-local-development/01-install-stctl.md)
- Kubernetes context configured for `dev` — see [Configure your local Kubernetes context](../set-up-local-development/02-configure-kubernetes.md)
- Docker installed and running locally

---

## Next steps after this group

- [Connect a device for remote access](../connect-first-device/index.md)
- [How do I view the session audit log?](../../observability/how-to-view-logs.md)
