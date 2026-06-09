---
persona: [developer]
task: [deployment, remote-access]
product: [smarttouch-cloud]
difficulty: advanced
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-06"
locale: en-US
translation-status: source
translated-from: ""
accessibility:
  reviewed: false
  images-have-alt-text: true
  color-independent: true
  has-text-diagrams: true
tags: [canary, deployment, istio, traffic-splitting, remote-access]
related:
  - docs/developers/deploy-release/how-to-deploy-service.md
  - docs/developers/deploy-release/how-to-promote.md
  - docs/developers/observability/how-to-view-logs.md
ai-retrieval-questions:
  - "How do I run a canary deployment on SmartTouch?"
  - "How do I split traffic between two versions of a service?"
  - "How do I gradually roll out the Remote Access Service?"
  - "How do I use Istio traffic splitting for a canary release?"
owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# How do I run a canary deployment?

> **Keyword:** How do I run a canary deployment on SmartTouch?

A canary deployment routes a percentage of traffic to a new service version while the current version continues to serve the remainder. SmartTouch uses Istio traffic splitting to manage the canary percentage. You increase the canary weight incrementally as you gain confidence in the new version.

---

## Goal

Deploy Remote Access Service v1.2.0 as a canary alongside v1.1.0, starting at 10% traffic, and promote to 100% once validated.

---

## Prerequisites

- v1.2.0 image built and pushed to Harbor
- `stctl` authenticated with `developer` or higher role
- Familiarity with the standard deployment workflow — see [How do I deploy a service?](./how-to-deploy-service.md)

---

## How canary traffic splitting works

```text
Incoming sessions
        ↓
Istio ingress gateway
        ↓
VirtualService weight rule
  ├── 10% → remote-access-service v1.2.0 (canary)
  └── 90% → remote-access-service v1.1.0 (stable)
```

Istio routes a percentage of new sessions to the canary. Existing open sessions are not affected — they remain on the version that established them.

---

## Steps

### Step 1 — Add the canary configuration to your SSD

```yaml
# smarttouch.yaml
service:
  name: remote-access-service
  version: "1.2.0"

deployment:
  image: harbor.smarttouch.io/myteam/remote-access-service:1.2.0
  replicas: 1              # Canary starts with a single replica

canary:
  enabled: true
  stable-version: "1.1.0"
  initial-weight: 10       # Percentage of new sessions routed to the canary
  analysis:
    metrics:
      - name: error-rate
        threshold: 1        # Canary is halted if error rate exceeds 1%
      - name: session-open-latency-p99
        threshold: 500      # Canary is halted if p99 session open latency exceeds 500ms
    interval: 5m            # Metrics are evaluated every 5 minutes
```

### Step 2 — Push and merge the canary configuration

Follow the standard pull request workflow. After merge, Argo CD deploys the canary alongside the stable version.

Verify both versions are running:

```bash
stctl pods --env dev --service remote-access-service
```

Expected:

```text
POD NAME                             VERSION   STATUS    READY
remote-access-service-stable-abc12   1.1.0     Running   1/1
remote-access-service-canary-def34   1.2.0     Running   1/1
```

### Step 3 — Monitor canary metrics

SmartTouch evaluates the canary automatically against the metrics defined in the SSD. View the current canary status:

```bash
stctl canary status --env dev --service remote-access-service
```

Expected output during a healthy canary run:

```text
Canary status:    progressing
Stable version:   1.1.0  (90% of sessions)
Canary version:   1.2.0  (10% of sessions)

Canary metrics (last 5m):
  error-rate:                 0.2%  ✔  (threshold: 1%)
  session-open-latency-p99:   120ms ✔  (threshold: 500ms)

Next evaluation: 4 minutes
```

### Step 4 — Increase the canary weight

When the canary metrics are healthy, increase the traffic percentage:

```bash
stctl canary set-weight \
  --env dev \
  --service remote-access-service \
  --weight 50
```

Repeat in increments: 10% → 50% → 100%. The recommended progression is:

| Weight | Duration before next increase |
| --- | --- |
| 10% | 15 minutes |
| 50% | 30 minutes |
| 100% | Canary promoted to stable |

### Step 5 — Promote the canary to stable

When you are confident the canary is healthy at 100%:

```bash
stctl canary promote --env dev --service remote-access-service
```

This command:

- Sets all traffic to v1.2.0
- Removes the v1.1.0 stable deployment
- Updates the SSD to remove the `canary` block

### Step 6 — Halt the canary if metrics degrade

If the canary error rate or latency exceeds the thresholds, halt it immediately:

```bash
stctl canary halt --env dev --service remote-access-service
```

This routes all traffic back to the stable version (v1.1.0) and stops the canary deployment. Investigate the issue before re-attempting.

---

## Validation

The canary deployment is healthy when:

| Check | Command | Expected |
| --- | --- | --- |
| Both versions running | `stctl pods --env dev --service remote-access-service` | One stable pod, one canary pod |
| Canary metrics healthy | `stctl canary status --env dev --service remote-access-service` | All metrics within threshold |
| Traffic split active | Same command | Percentages match configured weight |

---

## Troubleshooting

**`canary: enabled: feature not available`** during SSD validation

Canary deployments require Istio to be installed in your namespace. Contact your Platform Engineer to confirm Istio is enabled for your team's namespace.

### Canary automatically halted

The metrics thresholds were exceeded. View the canary analysis logs:

```bash
stctl canary logs --env dev --service remote-access-service
```

Then view service logs to find the root cause:

```bash
stctl logs --env dev --service remote-access-service --version canary --since 30m
```

---

## Next steps

- [How do I promote a release to production?](./how-to-promote.md)
- [How do I view logs for my service?](../observability/how-to-view-logs.md)
