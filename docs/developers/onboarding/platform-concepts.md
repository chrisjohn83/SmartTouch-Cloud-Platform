---
persona: [developer]
task: [getting-started, remote-access]
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
tags: [onboarding, concepts, remote-access, architecture, ssd, environments, gitops]
related:
  - docs/developers/onboarding/index.md
  - docs/developers/onboarding/authentication.md
  - docs/developers/secrets-config/ssd-schema-reference.md
ai-retrieval-questions:
  - "What are the key concepts in SmartTouch?"
  - "How does remote access work in SmartTouch?"
  - "What is the SmartTouch platform architecture?"
  - "What is an SSD in SmartTouch?"
  - "What are the three environments in SmartTouch?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Platform concepts

> **Keyword:** What are the key concepts in SmartTouch?

This page explains the six concepts you need to understand before you start the onboarding journey. Each concept maps directly to a step or term you will encounter in [First API call](./first-api-call.md).

---

## 1. The Remote Access Service and the Remote Access Agent

SmartTouch remote access has two parts:

**Remote Access Service** — a platform service deployed on Kubernetes that runs the session broker. Developers and automated systems connect to it.

**Remote Access Agent** — a lightweight process that runs on each IoT device. On startup, the agent dials an outbound WebSocket connection to the session broker. No inbound ports are required on the device.

```
Device
  └── Remote Access Agent  →  (outbound WebSocket, port 8443)
                                        ↓
                              SmartTouch Remote Access Service
                              (session broker)
                                        ↑
                              Your workstation / API client
                              (stctl or REST API)
```

**Why this matters:** When you call `POST /remote-access/sessions`, the platform routes your terminal through the broker to the agent on the device. The session exists only for the duration you keep it open. The device does not need a public IP address or open inbound firewall rules.

---

## 2. Devices and device IDs

A **device** is any IoT unit registered with the platform — physical hardware or a simulated device. Each device has a unique **device ID** (for example, `sensor-001`) that is set when the device is provisioned.

The device ID is the primary identifier you pass to API calls and CLI commands:

```bash
stctl device get sensor-001
stctl remote-access open sensor-001 --protocol diagnostics
```

In REST API calls:

```bash
GET /v1/devices/sensor-001
POST /v1/remote-access/sessions  (body: {"device_id": "sensor-001", ...})
```

Devices are registered automatically the first time the Remote Access Agent connects to the broker using its TLS certificate.

---

## 3. Session protocols

A remote access session uses one of three **protocols**. Each protocol grants a different level of access to the device.

| Protocol | What you can do | Minimum role required |
| --- | --- | --- |
| `diagnostics` | Run read-only diagnostic commands on the device | developer |
| `shell` | Full interactive shell on the device | platform-engineer |
| `file-transfer` | Upload and download files to/from the device | administrator |

During onboarding you will use the `diagnostics` protocol — it requires only the `developer` role and is safe to use in all environments.

Only one session per protocol per device can be open at the same time.

---

## 4. The Service Spec Definition (SSD)

The **Service Spec Definition (SSD)** is a `smarttouch.yaml` file that defines everything about a deployable service: its container image, replica count, environment configuration, secrets, observability settings, remote access rules, and canary strategy.

Developers create an SSD and commit it to Git. Argo CD watches the Git repository and automatically deploys the service when the SSD changes.

You do not write raw Kubernetes YAML. The platform translates the SSD into the underlying Kubernetes resources.

A minimal SSD for the Remote Access Service looks like this:

```yaml
service:
  name: remote-access-service
  image: harbor.smarttouch.local/library/remote-access-service:1.4.2

deployment:
  replicas: 2

remote-access:
  enabled: true
  broker-url: "wss://broker.smarttouch.local:8443"
  protocols:
    - diagnostics
    - shell
```

The SSD is not relevant to the REST API onboarding journey, but you will use it when you deploy your own services.

---

## 5. Three environments

SmartTouch has three deployment environments that map to stages of the development lifecycle.

| Environment | Purpose | Deploys when |
| --- | --- | --- |
| `dev` | Active development and testing | Every push to a feature branch |
| `staging` | Integration validation before production | On merge to `main` |
| `prod` | Live services | On a tagged release, with manual approval |

Most API calls require you to target an environment. In `stctl`, you pass `--env`:

```bash
stctl device list --env staging
stctl remote-access open sensor-001 --protocol diagnostics --env dev
```

In REST API calls, the environment is implicit — the base URL points to the correct environment cluster. Ask your Platform Engineer for the base URL of each environment.

During onboarding, use `dev` unless your Platform Engineer has told you otherwise.

---

## 6. Authentication and bearer tokens

Every API call requires a **bearer token** — a short-lived credential that proves your identity.

You obtain a token by authenticating with `stctl`:

```bash
stctl auth login   # opens a browser SSO window
stctl auth token   # prints the token to stdout
```

The token is passed in the `Authorization` header of every REST API request:

```text
Authorization: Bearer <token>
```

Tokens expire after 8 hours. `stctl` refreshes them automatically for CLI commands. For REST API calls you must re-run `stctl auth token` to get a fresh token when yours expires.

---

## Concept map

The six concepts connect like this:

```
You (developer role)
  └── bearer token → authenticates your identity
        └── REST API / stctl
              └── targets a device ID in an environment
                    └── device runs the Remote Access Agent
                          └── agent connects via outbound WebSocket to the session broker
                                └── you open a session using a protocol
```

---

## Next step

[Authentication →](./authentication.md)
