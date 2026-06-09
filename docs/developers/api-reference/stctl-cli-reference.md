---
persona: [developer]
task: [remote-access, deployment, observability, secrets, device-management]
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
tags: [stctl, cli, reference, remote-access, deployment, secrets, observability]
related:
  - docs/developers/api-reference/rest-api.md
  - docs/developers/deploy-release/how-to-deploy-service.md
  - docs/developers/observability/how-to-view-logs.md
ai-retrieval-questions:
  - "What stctl commands are available?"
  - "How do I use stctl to open a remote access session?"
  - "What is the stctl CLI?"
  - "How do I authenticate with stctl?"
  - "What flags does stctl remote-access open support?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# 'stctl' CLI reference

> **Keyword:** What 'stctl' commands are available?

`stctl` is the SmartTouch command-line interface. It provides commands for deploying services, managing remote access sessions, inspecting logs and traces, and administering secrets and configuration.

---

## Installation

```bash
# macOS (Homebrew)
brew install smarttouch/tap/stctl

# Linux (binary)
curl -sSL https://releases.smarttouch.io/stctl/install.sh | bash

# Verify installation
stctl version
```

---

## Global flags

These flags apply to all commands.

| Flag | Type | Description |
| --- | --- | --- |
| `--context` | string | Platform context to use (overrides `STCTL_CONTEXT` 'env' var) |
| `--namespace` | string | Kubernetes 'namespace' (overrides `STCTL_NAMESPACE` 'env' var) |
| `--output`, `-o` | string | Output format: `text` (default), `json`, `yaml` |
| `--quiet`, `-q` | 'boolean' | Suppress informational output; print only results |
| `--debug` | 'boolean' | Enable verbose debug logging |
| `--help`, `-h` | 'boolean' | Show help for any command |

---

## auth

Manage authentication tokens.

### auth login

Authenticate with the SmartTouch platform and store credentials locally.

```bash
stctl auth login [--context <name>]
```

Opens a browser window for SSO login. On success, stores a token in `~/.stctl/credentials`.

### auth logout

Remove stored credentials for the current context.

```bash
stctl auth logout
```

### auth token

Print the current bearer token. Use this with `curl` or other HTTP clients.

```bash
stctl auth token
```

### auth status

Show the current authentication state, token expiry, and context.

```bash
stctl auth status
```

**Example output:**

```text
Context:    production
User:       alice@example.com
Token:      valid (expires in 6h 42m)
Namespace:  default
```

---

## device

Manage and inspect IoT devices.

### device list

List all devices visible to the current user.

```bash
stctl device list [--status <online|offline|unknown>] [--fleet <name>]
```

**Flags:**

| Flag | Description |
| --- | --- |
| `--status` | Filter by agent status |
| `--fleet` | Filter by fleet label |

**Example:**

```bash
stctl device list --status online
```

**Example output:**

```text
ID           DISPLAY NAME              FLEET           AGENT STATUS   LAST SEEN
sensor-001   Temperature Sensor 001   factory-floor   online         2m ago
sensor-002   Humidity Sensor 002      factory-floor   online         5m ago
```

### device get

Show details for a single device.

```bash
stctl device get <device_id>
```

**Example:**

```bash
stctl device get sensor-001
```

### device agent-status

Show the Remote Access Agent connection state for a device.

```bash
stctl device agent-status <device_id>
```

**Example output:**

```text
Device:        sensor-001
Agent status:  online
Connected at:  2026-06-08 08:55:32 UTC
Broker:        wss://broker.smarttouch.local:8443
Latency:       12ms
```

---

## remote-access

Manage remote access sessions to IoT devices.

### remote-access open

Open a new remote access session to a device.

```bash
stctl remote-access open <device_id> \
  --protocol <shell|diagnostics|file-transfer> \
  [--ttl <duration>]
```

**Flags:**

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--protocol` | string | `diagnostics` | Session protocol |
| `--ttl` | duration | `1h` | Session time-to-live (for example, `30m`, `2h`) |

**Protocol permission requirements:**

| Protocol | Minimum role |
| --- | --- |
| `diagnostics` | developer |
| `shell` | platform-engineer |
| `file-transfer` | administrator |

**Example—open a diagnostics session:**

```bash
stctl remote-access open sensor-001 --protocol diagnostics
```

**Example output:**

```text
Opening diagnostics session to sensor-001...
Session ID:   sess-9c4d2e
Protocol:     diagnostics
Expires at:   2026-06-08 10:05:00 UTC

Connected. Type 'exit' to close the session.
[sensor-001 diagnostics]$
```

**Example—open a shell session:**

```bash
stctl remote-access open sensor-001 --protocol shell --ttl 30m
```

### remote-access list

List active and recent remote access sessions.

```bash
stctl remote-access list [--device <device_id>] [--status <open|closed>]
```

**Example:**

```bash
stctl remote-access list --device sensor-001 --status open
```

**Example output:**

```text
SESSION ID   DEVICE       PROTOCOL      STATUS   USER                   OPENED
sess-9c4d2e  sensor-001   diagnostics   open     alice@example.com      10m ago
```

### remote-access close

Close an active session.

```bash
stctl remote-access close <session_id>
```

**Example:**

```bash
stctl remote-access close sess-9c4d2e
```

---

## deploy

Deploy a service using a Service Spec Definition (SSD) file.

### deploy apply

Apply an SSD file to the platform. Creates or updates the service.

```bash
stctl deploy apply -f <path-to-smarttouch.yaml> [--env <dev|staging|prod>]
```

**Flags:**

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `-f` | string | — | Path to `smarttouch.yaml` |
| `--env` | string | `dev` | Target environment |
| `--dry-run` | 'boolean' | false | Validate the SSD without applying |

**Example:**

```bash
stctl deploy apply -f smarttouch.yaml --env staging
```

### deploy status

Show the 'rollout' status of a deployed service.

```bash
stctl deploy status <service_name> [--env <dev|staging|prod>]
```

**Example output:**

```text
Service:      remote-access-service
Environment:  staging
Status:       healthy
Revision:     v1.4.2
Replicas:     3/3 ready
Last updated: 4m ago
```

---

## rollback

Roll back a service to a previous revision.

```bash
stctl rollback <service_name> [--to <revision>] [--env <dev|staging|prod>]
```

**Flags:**

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--to` | string | previous | Target revision tag or hash |
| `--env` | string | `dev` | Target environment |

**Example—roll back to the previous revision:**

```bash
stctl rollback remote-access-service --env staging
```

**Example—roll back to a specific revision:**

```bash
stctl rollback remote-access-service --to v1.4.1 --env staging
```

---

## canary

Manage canary deployments.

### canary status

Show current canary traffic split for a service.

```bash
stctl canary status <service_name> [--env <dev|staging|prod>]
```

**Example output:**

```text
Service:  remote-access-service
Stable:   90%  (v1.4.1)
Canary:   10%  (v1.4.2)
```

### canary set-weight

Adjust the percentage of traffic routed to the canary version.

```bash
stctl canary set-weight <service_name> --weight <0-100> [--env <dev|staging|prod>]
```

**Example—increase canary to 50%:**

```bash
stctl canary set-weight remote-access-service --weight 50 --env staging
```

### canary promote

Promote the canary version to stable (100% traffic).

```bash
stctl canary promote <service_name> [--env <dev|staging|prod>]
```

### canary halt

Stop the canary and return all traffic to the stable version.

```bash
stctl canary halt <service_name> [--env <dev|staging|prod>]
```

---

## secrets

Manage service secrets stored in HashiCorp Vault.

### secrets set

Set a secret value for a service.

```bash
stctl secrets set <service_name> <key>=<value> [--env <dev|staging|prod>]
```

**Example:**

```bash
stctl secrets set remote-access-service BROKER_TLS_CERT=@./broker-tls.crt --env staging
```

### secrets list

List secret keys (not values) for a service.

```bash
stctl secrets list <service_name> [--env <dev|staging|prod>]
```

**Example output:**

```text
Service:      remote-access-service
Environment:  staging

KEY                     LAST UPDATED
BROKER_TLS_CERT         2026-06-07 14:22:00 UTC
SESSION_SIGNING_KEY     2026-06-01 09:00:00 UTC
```

---

## Configuration

Manage environment-specific configuration values.

### Config show

Show the active configuration for a service in a given environment.

```bash
stctl config show <service_name> [--env <dev|staging|prod>]
```

**Example output:**

```text
Service:      remote-access-service
Environment:  staging

KEY                         VALUE
LOG_LEVEL                   info
MAX_SESSIONS_PER_DEVICE     10
SESSION_TTL_SECONDS         3600
BROKER_URL                  wss://broker.smarttouch.local:8443
```

---

## Logs

View and stream service logs.

### Log for a service

Stream or retrieve logs for a service.

```bash
stctl logs <service_name> \
  [--env <dev|staging|prod>] \
  [--level <debug|info|warn|error>] \
  [--since <duration>] \
  [--filter <key=value>] \
  [--pod <pod_name>] \
  [--follow]
```

**Flags:**

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--env` | string | `dev` | Target environment |
| `--level` | string | — | Filter by log level |
| `--since` | duration | `15m` | Return logs from this far back |
| `--filter` | string | — | Filter by structured field (for example, `sessionId=sess-9c4d2e`) |
| `--pod` | string | — | Filter to a specific pod |
| `--follow`, `-f` | 'boolean' | false | Stream logs in real time |

**Example—view error logs for the last hour:**

```bash
stctl logs remote-access-service --level error --since 1h --env staging
```

**Example—filter logs by session ID:**

```bash
stctl logs remote-access-service --filter sessionId=sess-9c4d2e
```

**Example—stream logs in real time:**

```bash
stctl logs remote-access-service --follow
```

---

## trace

Inspect distributed traces for requests and sessions.

### trace open

Open a trace in the 'Grafana' trace viewer.

```bash
stctl trace open <trace_id>
```

**Example:**

```bash
stctl trace open abc123def456
```

### trace list

List recent traces for a service.

```bash
stctl trace list <service_name> \
  [--env <dev|staging|prod>] \
  [--since <duration>] \
  [--session <session_id>]
```

**Example:**

```bash
stctl trace list remote-access-service --since 30m --session sess-9c4d2e
```

---

## status

Show overall platform health.

```bash
stctl status [--env <dev|staging|prod>]
```

**Example output:**

```text
Environment:  staging

COMPONENT                  STATUS
Remote Access Service      healthy
EMQX MQTT Broker           healthy
Vault                      healthy
Argo CD                    healthy
Prometheus                 healthy
Loki                       healthy
Jaeger                     healthy
```

---

## pods

Inspect Kubernetes pods for a service.

```bash
stctl pods <service_name> [--env <dev|staging|prod>]
```

**Example output:**

```text
POD                                  STATUS    RESTARTS   AGE
remote-access-service-78d4b-lx9rp   Running   0          22h
remote-access-service-78d4b-mq2tk   Running   0          22h
remote-access-service-78d4b-p6fvs   Running   0          22h
```

---

## exec

Execute a command inside a running service pod. Requires platform-engineer role.

```bash
stctl exec <service_name> -- <command> [--env <dev|staging|prod>] [--pod <pod_name>]
```

**Example:**

```bash
stctl exec remote-access-service -- env | grep BROKER
```

---

## simulator

Manage the local device simulator for development and testing.

### simulator start

Start a simulated device that connects to the local or development environment.

```bash
stctl simulator start \
  --device-id <id> \
  [--remote-access] \
  [--env <dev|staging>]
```

**Flags:**

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--device-id` | string | — | Device ID to register |
| `--remote-access` | 'boolean' | false | Enable the Remote Access Agent on the simulator |
| `--env` | string | `dev` | Target environment |

**Example:**

```bash
stctl simulator start --device-id sensor-001 --remote-access
```

### simulator stop

Stop and 'deregister' a simulated device.

```bash
stctl simulator stop --device-id <id>
```

---

## Environment variables

`stctl` respects the following environment variables. Command-line flags take precedence.

| Variable | Description |
| --- | --- |
| `STCTL_CONTEXT` | Default context name |
| `STCTL_NAMESPACE` | Default Kubernetes 'namespace' |
| `STCTL_TOKEN` | Bearer token (bypasses stored credentials) |
| `STCTL_OUTPUT` | Default output format (`text`, `json`, `yaml`) |
| `STCTL_DEBUG` | Set to `1` to enable debug logging |

---

## Configuration file

`stctl` reads from `~/.stctl/config.yaml` for default context and 'namespace' settings.

```yaml
current-context: production
contexts:
  - name: production
    platform-url: https://api.smarttouch.example.com
    namespace: default
  - name: local
    platform-url: https://api.smarttouch.local
    namespace: dev
```

---

## Related

- [SmartTouch REST API reference](./rest-api.md)
- [How do I deploy a service?](../deploy-release/how-to-deploy-service.md)
- [How do I view logs for my service?](../observability/how-to-view-logs.md)
- [How do I trace a request end-to-end?](../observability/how-to-trace-request.md)
