---
persona: [developer]
task: [getting-started, remote-access, authentication]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-08"
locale: en-US
translation-status: source
translated-from: ""
accessibility:
  reviewed: false
  images-have-alt-text: true
  color-independent: true
  has-text-diagrams: true
tags: [onboarding, getting-started, developer, authentication, remote-access, first-api-call]
related:
  - docs/developers/index.md
  - docs/developers/api-reference/rest-api.md
  - docs/developers/api-reference/stctl-cli-reference.md
ai-retrieval-questions:
  - "How do I get started as a SmartTouch developer?"
  - "What is the developer onboarding path for SmartTouch?"
  - "What do I need before I can use the SmartTouch API?"
  - "How do I make my first API call to SmartTouch?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Developer onboarding

> **Keyword:** How do I get started as a SmartTouch developer?

This section takes a new developer from zero to a working remote access session in under 30 minutes. No prior SmartTouch knowledge is required.

You will follow a single guided journey — from getting credentials to opening and closing a live session — using both the `stctl` CLI and the REST API side by side.

---

## The onboarding journey

```mermaid
Get credentials
      ↓
Generate a token
      ↓
Find a device
      ↓
Verify the device is online
      ↓
Open a remote access session
      ↓
Confirm success
      ↓
Close the session

```

Each step in [First API call](./first-api-call.md) shows the `stctl` command and the equivalent REST API call so you can use whichever fits your workflow.

---

## Onboarding documents

| Document | What it covers | Time |
| --- | --- | --- |
| [Prerequisites](./prerequisites.md) | Tools and access you need before starting | 5 min |
| [Platform concepts](./platform-concepts.md) | Key terms and how the platform fits together | 10 min |
| [Authentication](./authentication.md) | How to get credentials and generate tokens | 10 min |
| [First API call](./first-api-call.md) | The complete 7-step guided journey | 20 min |
| [Common errors](./common-errors.md) | Errors you may encounter and how to fix them | Reference |

**Recommended order:** Read Prerequisites and Platform Concepts first, then Authentication, then work through First API Call step by step.

---

## What you will be able to do after onboarding

- Authenticate with the SmartTouch platform using both `stctl` and the REST API.
- List devices and check whether a device agent is online.
- Open a `diagnostics` session to a device and confirm it is active.
- Close the session cleanly.
- Understand the error codes you will encounter during development.

---

## If you get stuck

- [Common errors](./common-errors.md) — covers the most frequent errors at each step of the journey.
- [Why is my device not connecting?](../troubleshooting/why-device-not-connecting.md) — agent and certificate issues.
- [stctl CLI reference](../api-reference/stctl-cli-reference.md) — full command reference.
- [SmartTouch REST API reference](../api-reference/index.md) — full endpoint reference.

---

## After onboarding

Once you have completed the journey, the rest of the developer section is task-based:

| Next topic | Link |
| --- | --- |
| Deploy a service | [How do I deploy a service?](../deploy-release/how-to-deploy-service.md) |
| Connect a physical device | [Connect a device for remote access](../get-started/connect-first-device/index.md) |
| Instrument your service | [How do I instrument my service?](../observability/how-to-instrument-service.md) |
| Manage secrets | [How do I manage secrets securely?](../secrets-config/how-to-manage-secrets.md) |
