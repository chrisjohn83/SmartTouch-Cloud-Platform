---
persona: [developer]
task: [device-connection, remote-access]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-06"
tags: [device, remote-access, remote-access-agent, certificate, session, getting-started]
related:
  - docs/developers/get-started/deploy-first-iot-service/index.md
  - docs/developers/get-started/set-up-local-development/index.md

ai-retrieval-questions:
  - "How do I connect a device for remote access?"
  - "How do I enable remote access on an IoT device?"
  - "How do I install the Remote Access Agent on a device?"
  - "How do I set up a device so I can access it remotely?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Connect a device for remote access

> **Keyword:** How do I connect a device for remote access?

This tutorial group walks you through the three steps required to make an IoT device reachable via SmartTouch remote access: provisioning its identity certificate, installing and configuring the Remote Access Agent, and verifying that shell and diagnostics sessions can be opened to it.

---

## What you will learn

- How to provision a device TLS certificate scoped for remote access
- How to install the Remote Access Agent on a device and configure it to connect to the SmartTouch session broker
- How to open and verify shell and diagnostics sessions to a live device

---

## How remote access works

The Remote Access Agent runs on each device and dials an outbound WebSocket connection to the SmartTouch Remote Access Service. Because the connection is outbound, sessions work through NAT and corporate firewalls without any special network configuration.

```
Device (outbound WebSocket)  →  Remote Access Service  ←  stctl / SmartTouch Console
```

When you open a session with `stctl remote-access open`, the platform routes your terminal through the broker to the agent on the device — creating a secure, authenticated tunnel for the duration of the session.

---

## Tutorial sequence

| Step | Tutorial | Time |
|---|---|---|
| 1 | [Provision a device certificate for remote access](./01-provision-certificate.md) | ~10 min |
| 2 | [Install the Remote Access Agent](./02-install-remote-access-agent.md) | ~15 min |
| 3 | [Open your first remote access session](./03-open-first-remote-session.md) | ~10 min |

**Total time:** ~35 minutes

---

## Prerequisites

- Remote Access Service deployed and running — see [Deploy the Remote Access Service](../deploy-first-iot-service/index.md)
- `stctl` authenticated with remote access permissions
- OpenSSL installed locally
- A physical or simulated device running Linux (use `stctl simulator start` for testing)

---

## Device simulator

```bash
stctl simulator start \
  --device-id sensor-001 \
  --remote-access
```

The simulator handles certificate provisioning and agent installation automatically. Use it to verify the end state quickly, or follow the tutorials to understand each step.

---

## Next steps after this group

- [How do I open a remote access session?](../../deploy-release/how-to-open-remote-session.md)
- [How do I view the session audit log?](../../observability/how-to-view-session-audit-log.md)
- [How do I manage sessions across multiple devices?](../../secrets-config/how-to-manage-sessions.md)
