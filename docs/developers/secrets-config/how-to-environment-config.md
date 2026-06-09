---
persona: [developer]
task: [configuration, remote-access, deployment]
product: [smarttouch-cloud]
difficulty: intermediate
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
tags: [configuration, environment, kustomize, configmap, remote-access]
related:
  - docs/developers/secrets-config/how-to-manage-secrets.md
  - docs/developers/secrets-config/ssd-schema-reference.md
ai-retrieval-questions:
  - "How do I use environment-specific configuration on SmartTouch?"
  - "How do I set different config values for dev, staging, and prod?"
  - "How do I use Kustomize overlays for SmartTouch?"
  - "How do I configure the Remote Access Service differently per environment?"
owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# How do I use environment-specific config?

> **Keyword:** How do I use environment-specific configuration on SmartTouch?

SmartTouch uses Kustomize overlays to manage per-environment configuration. Non-secret values (session limits, timeouts, feature flags) live in a `ConfigMap` per environment. Secret values live in Vault — see [How do I manage secrets securely?](./how-to-manage-secrets.md).

---

## Goal

Configure the Remote Access Service to use different session timeouts and concurrent session limits in `dev`, `staging`, and `prod`.

---

## Prerequisites

- The Remote Access Service SSD created and deployed to `dev`
- Familiarity with the standard deployment workflow

---

## Configuration layers

```text
smarttouch.yaml (SSD)       ← Default values for all environments
        +
k8s/overlays/dev/           ← Overrides for dev
k8s/overlays/staging/       ← Overrides for staging
k8s/overlays/prod/          ← Overrides for prod
```

Values in the overlay take precedence over the SSD defaults for that environment.

---

## Steps

### Step 1 — Define defaults in the SSD

```yaml
# smarttouch.yaml
remote-access:
  session-timeout: "30m"
  max-concurrent-sessions: 10
  idle-timeout: "5m"
```

These values apply to all environments unless overridden.

### Step 2 — Create environment-specific overrides

Create a ConfigMap patch for each environment that needs different values.

For `dev` (relaxed limits for testing):

```yaml
# k8s/overlays/dev/remote-access-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: remote-access-service-config
data:
  SESSION_TIMEOUT: "60m"
  MAX_CONCURRENT_SESSIONS: "5"
  IDLE_TIMEOUT: "15m"
```

For `prod` (tighter limits for security):

```yaml
# k8s/overlays/prod/remote-access-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: remote-access-service-config
data:
  SESSION_TIMEOUT: "30m"
  MAX_CONCURRENT_SESSIONS: "50"
  IDLE_TIMEOUT: "5m"
```

### Step 3 — Reference the ConfigMap in the SSD

```yaml
# smarttouch.yaml
config:
  from-configmap: remote-access-service-config
  env-vars:
    - SESSION_TIMEOUT
    - MAX_CONCURRENT_SESSIONS
    - IDLE_TIMEOUT
```

SmartTouch injects the ConfigMap values as environment variables into the pod at deploy time.

### Step 4 — Read config values in your service code

```javascript
const sessionTimeout = process.env.SESSION_TIMEOUT || '30m';
const maxSessions    = parseInt(process.env.MAX_CONCURRENT_SESSIONS || '10');
const idleTimeout    = process.env.IDLE_TIMEOUT || '5m';
```

### Step 5 — Verify the correct config is applied

```bash
stctl config show --env dev --service remote-access-service
```

Expected output:

```text
Environment: dev
ConfigMap:   remote-access-service-config

SESSION_TIMEOUT:          60m
MAX_CONCURRENT_SESSIONS:  5
IDLE_TIMEOUT:             15m
```

---

## Validation

```bash
stctl config show --env dev --service remote-access-service
# Values match the dev overlay

stctl config show --env prod --service remote-access-service
# Values match the prod overlay
```

---

## Troubleshooting

**Service is using SSD default values instead of overlay values**

The ConfigMap patch may not have been applied. Check whether the overlay file is referenced in `k8s/overlays/dev/kustomization.yaml`:

```yaml
resources:
  - ../../base
patches:
  - path: remote-access-config.yaml
```

If the patch file is not listed, add it and redeploy.

---

## Next steps

- [How do I manage secrets securely?](./how-to-manage-secrets.md)
- [What is the SSD schema?](./ssd-schema-reference.md)
