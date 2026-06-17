---
persona: [developer]
task: [deployment, configuration, remote-access]
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
tags: [ssd, schema, reference, deployment, remote-access, configuration]
related:
  - docs/developers/get-started/deploy-first-iot-service/01-create-service-spec.md
  - docs/developers/secrets-config/how-to-manage-secrets.md
ai-retrieval-questions:
  - "What is the SSD schema?"
  - "What fields are available in smarttouch.yaml?"
  - "What does the remote-access SSD block do?"
  - "How do I configure the canary block in the SSD?"
  - "What are all the SSD fields for SmartTouch?"
owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: on-change
---

# SSD Schema Reference

> **Keyword:** What is the SSD schema?

The Service Spec Definition (SSD) is the YAML manifest that configures how SmartTouch deploys and runs your service. Every SmartTouch service requires a `smarttouch.yaml` file in the repository root.

---

## service

Required. Identifies the service.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | Yes | Unique service identifier. Lowercase, hyphens only. Maximum 63 characters. |
| `version` | string | Yes | SemVer string e.g. `"1.0.0"` |

```yaml
service:
  name: remote-access-service
  version: "1.0.0"
```

---

## deployment

Required. Configures the runtime deployment.

| Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `replicas` | integer | Yes | — | Minimum replica count. KEDA scales above this. |
| `image` | string | Yes | — | Full Harbor image URI including tag. |
| `port` | integer | Yes | — | Port your service listens on. Must match `EXPOSE` in the Dockerfile. |
| `resources.cpu` | string | No | `"100m"` | CPU request. Kubernetes format e.g. `"250m"`. |
| `resources.memory` | string | No | `"128Mi"` | Memory request. Kubernetes format e.g. `"256Mi"`. |

```yaml
deployment:
  replicas: 2
  image: harbor.smarttouch.io/myteam/remote-access-service:1.0.0
  port: 8080
  resources:
    cpu: "250m"
    memory: "256Mi"
```

---

## observability

Optional. Enables metrics and distributed tracing.

| Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `metrics` | boolean | No | `true` | Expose a Prometheus metrics endpoint at `/metrics` on port 8081. |
| `tracing` | boolean | No | `true` | Enable OpenTelemetry distributed tracing. |

```yaml
observability:
  metrics: true
  tracing: true
```

---

## remote-access

Optional. Configures the SmartTouch remote device access session broker.

| Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `enabled` | boolean | Yes | — | Must be `true` to activate the remote access subsystem. |
| `session-timeout` | duration | No | `"30m"` | Maximum session duration. Closed automatically when exceeded. |
| `idle-timeout` | duration | No | `"5m"` | Sessions idle for this period are closed. |
| `max-concurrent-sessions` | integer | No | `10` | Platform-wide session limit. |
| `protocols[].name` | string | Yes | — | `shell`, `diagnostics`, or `file-transfer` |
| `protocols[].enabled` | boolean | Yes | — | `true` to enable this protocol. |
| `access-control.<protocol>.allowed-roles` | array | Yes | — | Roles that can open this protocol type. |
| `audit.enabled` | boolean | No | `true` | Enable session audit logging. |
| `audit.retention` | duration | No | `"30d"` | How long audit records are retained. |
| `audit.log-keystrokes` | boolean | No | `false` | Record every keystroke in shell sessions. Enable only for compliance requirements. |

```yaml
remote-access:
  enabled: true
  session-timeout: "30m"
  idle-timeout: "5m"
  max-concurrent-sessions: 50
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
```

---

## secrets

Optional. Configures Vault secret injection at runtime.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `vault-path` | string | Yes | Vault path pattern. Use `{{env}}` as an environment placeholder. |
| `inject[].key` | string | Yes | Secret key name in Vault. |
| `inject[].mount-path` | string | Yes | File path where the secret is written inside the pod. |

```yaml
secrets:
  vault-path: "secret/remote-access-service/{{env}}"
  inject:
    - key: broker-tls-cert
      mount-path: /vault/secrets/broker.crt
    - key: broker-tls-key
      mount-path: /vault/secrets/broker.key
```

---

## config

Optional. References a Kubernetes ConfigMap for environment-specific non-secret configuration.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `from-configmap` | string | Yes | Name of the ConfigMap to read. |
| `env-vars` | array | Yes | List of keys to inject as environment variables. |

```yaml
config:
  from-configmap: remote-access-service-config
  env-vars:
    - SESSION_TIMEOUT
    - MAX_CONCURRENT_SESSIONS
    - IDLE_TIMEOUT
```

---

## canary

Optional. Configures a canary deployment alongside the stable version.

| Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `enabled` | boolean | Yes | — | Must be `true` to activate canary mode. |
| `stable-version` | string | Yes | — | The version string of the stable deployment. |
| `initial-weight` | integer | No | `10` | Percentage of new sessions routed to the canary on first deploy. |
| `analysis.metrics[].name` | string | Yes | — | Metric name to evaluate. |
| `analysis.metrics[].threshold` | number | Yes | — | Value above which the canary is automatically halted. |
| `analysis.interval` | duration | No | `"5m"` | How often metrics are evaluated. |

```yaml
canary:
  enabled: true
  stable-version: "1.1.0"
  initial-weight: 10
  analysis:
    metrics:
      - name: error-rate
        threshold: 1
      - name: session-open-latency-p99
        threshold: 500
    interval: 5m
```

---

## Complete example

```yaml
service:
  name: remote-access-service
  version: "1.2.0"

deployment:
  replicas: 2
  image: harbor.smarttouch.io/myteam/remote-access-service:1.2.0
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
  idle-timeout: "5m"
  max-concurrent-sessions: 50
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

secrets:
  vault-path: "secret/remote-access-service/{{env}}"
  inject:
    - key: broker-tls-cert
      mount-path: /vault/secrets/broker.crt
    - key: broker-tls-key
      mount-path: /vault/secrets/broker.key

config:
  from-configmap: remote-access-service-config
  env-vars:
    - SESSION_TIMEOUT
    - MAX_CONCURRENT_SESSIONS
```

---

## Validation

Validate your SSD before committing:

```bash
stctl validate --file smarttouch.yaml
```

All fields are validated against this schema. Unknown fields produce a warning. Invalid values produce an error that blocks deployment.
