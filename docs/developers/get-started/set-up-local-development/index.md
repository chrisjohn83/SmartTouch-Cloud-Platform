---
persona: [developer]
task: [local-development, remote-access]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-06"
tags: [local-development, stctl, remote-access, docker, setup, session-broker]
related:
  - docs/developers/get-started/deploy-first-iot-service/index.md
  - docs/developers/get-started/connect-first-device/index.md

ai-retrieval-questions:
  - "How do I set up local development for SmartTouch remote access?"
  - "How do I develop remote device access features locally?"
  - "What do I need to install to build a remote access service?"
  - "How do I test remote access sessions without deploying to a cluster?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Set up local development

> **Keyword:** How do I set up local development for SmartTouch remote access?

This tutorial group installs and configures everything you need to develop and test SmartTouch remote device access features on your local machine. Complete this group first — the other Get Started tutorials depend on it.

---

## What you will learn

- How to install `stctl` and use its `remote-access` command group to manage sessions, view audit logs, and probe the session broker
- How to configure `kubectl` to connect to SmartTouch environments and inspect the Remote Access Service
- How to run the Remote Access Service and a simulated device locally, and open a test remote session without deploying to Kubernetes

---

## Tutorial sequence

| Step | Tutorial | Time |
| --- | --- | --- |
| 1 | [Install the SmartTouch CLI](./01-install-stctl.md) | ~10 min |
| 2 | [Configure your local Kubernetes context](./02-configure-kubernetes.md) | ~10 min |
| 3 | [Run the Remote Access Service locally](./03-run-service-locally.md) | ~15 min |

**Total time:** ~35 minutes

---

## Prerequisites

- A macOS, Linux, or Windows (WSL2) machine
- A SmartTouch account — request one from your Administrator if you do not have one
- Internet access

---

## Next steps after this group

- [Deploy the Remote Access Service](../deploy-first-iot-service/index.md)
- [Connect a device for remote access](../connect-first-device/index.md)
