---
persona: [developer]
task: [getting-started, authentication]
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
  has-text-diagrams: false
tags: [onboarding, prerequisites, stctl, developer, getting-started]
related:
  - docs/developers/onboarding/index.md
  - docs/developers/onboarding/authentication.md
  - docs/developers/api-reference/stctl-cli-reference.md
ai-retrieval-questions:
  - "What do I need before I can use SmartTouch?"
  - "What tools do I need to install before onboarding?"
  - "What access do I need to get started with SmartTouch?"
  - "How do I install stctl?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Prerequisites

> **Keyword:** What do I need before I can use SmartTouch?

Before you start the [onboarding journey](./first-api-call.md), confirm that you have everything in this checklist. Each item links to setup instructions if you need them.

---

## Access

| Requirement | How to get it |
| --- | --- |
| SmartTouch platform account | You must request access from your Administrator or Platform Engineer. You will receive an email invitation with SSO login instructions. |
| `developer` role or higher | You must verify your role with `stctl auth status` after login. The `developer` role is required to open `diagnostics` sessions. |
| A registered device or simulator access | You must ask your Platform Engineer for a registered device ID, or use the built-in simulator. |

---

## Tools

### stctl CLI

`stctl` is required for authentication and for running CLI versions of each step in the guided journey.

**Install on macOS:**

```bash
brew install smarttouch/tap/stctl
```

**Install on Linux:**

```bash
curl -sSL https://releases.smarttouch.io/stctl/install.sh | bash
```

**Verify the installation:**

```bash
stctl version
```

Expected output:

```text
stctl version 1.4.2
Platform API: https://api.smarttouch.local/v1
```

If `stctl version` fails, confirm that `~/.local/bin` (Linux) or `/usr/local/bin` (macOS) is on your `PATH`.

---

### curl

`curl` is used in this guide for all REST API examples. Most operating systems include it by default.

**Verify:**

```bash
curl --version
```

Any version `7.x` or later is sufficient. If `curl` is not available, use any HTTP client (Postman, HTTPie, or your preferred language's HTTP library) — the examples are standard REST calls.

---

### OpenSSL

OpenSSL is required only if you provision device certificates manually. It is not required for the onboarding journey itself.

**Verify:**

```bash
openssl version
```

---

### A terminal emulator

The onboarding journey uses a terminal. Any standard shell works: `bash`, `zsh`, `PowerShell` (Windows), or `Terminal` (macOS).

---

## Network access

Your workstation must be able to reach the following endpoints:

| Endpoint | Port | Protocol | Used for |
| --- | --- | --- | --- |
| `api.<your-platform-domain>` | 443 | HTTPS | SmartTouch REST API |
| `broker.<your-platform-domain>` | 8443 | WSS | Remote access session broker |

Ask your Platform Engineer for the actual hostname values for your environment. For the default local development environment the hostnames are `api.smarttouch.local` and `broker.smarttouch.local`.

If your workstation is behind a corporate proxy or VPN, confirm that outbound HTTPS on port 443 and WSS on port 8443 are allowed.

---

## Using the device simulator

If you do not have a physical device available, start the built-in device simulator. It creates a virtual device that behaves identically to a real one for all steps in the onboarding journey.

```bash
stctl simulator start \
  --device-id onboarding-device-01 \
  --remote-access
```

Expected output:

```text
Starting simulator...
Device ID:     onboarding-device-01
Agent status:  online
Broker:        wss://broker.smarttouch.local:8443
Remote access: enabled
```

Use `onboarding-device-01` as the device ID throughout the onboarding journey.

Stop the simulator when you are done:

```bash
stctl simulator stop --device-id onboarding-device-01
```

---

## Checklist summary

Before continuing to [Authentication](./authentication.md), confirm:

- [ ] Platform account created and SSO invitation received
- [ ] `stctl` installed and `stctl version` returns output
- [ ] `curl` available
- [ ] Network can reach the platform API and broker endpoints
- [ ] A device ID is available (physical device or simulator running)

---

## Next step

[Authentication →](./authentication.md)
