---
persona: [developer]
task: [local-development, remote-access]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-06"
tags: [local-development, docker-compose, remote-access, session, simulated-device, testing]
sequence: 3
part-of: set-up-local-development
related:
  - docs/developers/get-started/set-up-local-development/02-configure-kubernetes.md
  - docs/developers/get-started/deploy-first-iot-service/index.md

ai-retrieval-questions:
  - "How do I run the Remote Access Service locally?"
  - "How do I test a remote access session without deploying to a cluster?"
  - "How do I simulate a device for remote access testing?"
  - "How do I open a local remote access session?"
  - "How do I run the SmartTouch remote access stack locally?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Run the Remote Access Service locally

> **Keyword:** How do I run the Remote Access Service locally?
> **Part of:** [Set up local development](./index.md) — Step 3 of 3

The SmartTouch local stack includes a Remote Access Service container and a device simulator pre-configured with the Remote Access Agent. Together they let you open, test, and close remote sessions entirely on your machine — without deploying to a Kubernetes cluster or connecting real hardware.

---

## Goal

Start the local Remote Access Service, launch a simulated device with the Remote Access Agent, and open a diagnostics session to the simulated device.

---

## Prerequisites

- Completed [Configure your local Kubernetes context](./02-configure-kubernetes.md)
- Docker and Docker Compose installed
- A Remote Access Service repository with a `Dockerfile` and `smarttouch.yaml`

---

## Steps

### Step 1 — Initialise the local stack

```bash
stctl local init
```

Creates two files:

```text
docker-compose.local.yml    ← Remote Access Service + simulated device
.env.local                  ← Local connection strings (git-ignored)
```

### Step 2 — Review the local stack

The local stack for remote access includes the session broker, a simulated device running the Remote Access Agent, and a lightweight audit log sink:

```yaml
services:
  remote-access-service:
    image: smarttouch/remote-access-service:latest
    ports: ["8080:8080", "8081:8081"]
    environment:
      AUTH_MODE: local              # Bypasses Vault for local development
      AUDIT_SINK: local-audit       # Sends audit events to the local sink

  local-audit:
    image: smarttouch/audit-sink:latest
    ports: ["9001:9001"]           # Query audit events at localhost:9001

  simulated-device:
    image: smarttouch/device-simulator:latest
    environment:
      DEVICE_ID: sim-device-001
      REMOTE_ACCESS_BROKER: ws://remote-access-service:8080
      PROTOCOLS: shell,diagnostics  # Protocols the simulator accepts
```

The `simulated-device` container runs a full Remote Access Agent connected to the local broker. It accepts `shell` and `diagnostics` sessions and responds as a real device would.

### Step 3 — Start the local stack

```bash
docker compose -f docker-compose.local.yml up -d
```

Wait for all containers to become healthy:

```bash
docker compose -f docker-compose.local.yml ps
```

All three should show `healthy` or `running`.

### Step 4 — Verify the local broker

```bash
stctl remote-access status --env local
```

Expected output:

```text
Remote Access Service:  available (local)
Session broker:         ready
Protocols:              shell, diagnostics
Active sessions:        0
```

### Step 5 — Open a local diagnostics session

```bash
stctl remote-access open \
  --device sim-device-001 \
  --protocol diagnostics \
  --env local
```

Expected output — a live stream of simulated device diagnostics:

```text
✔  Session opened: sess-local-001
Device: sim-device-001  Protocol: diagnostics  Timeout: 30m

--- Device Diagnostics Stream ---
cpu_usage:       12%
memory_used:     128MB / 512MB
uptime:          00:04:32
network_rx:      1.2 KB/s
network_tx:      0.8 KB/s
agent_version:   1.4.2
--- (refreshes every 5s — press Ctrl+C to close) ---
```

Press `Ctrl+C` to close the session.

### Step 6 — Open a local shell session

```bash
stctl remote-access open \
  --device sim-device-001 \
  --protocol shell \
  --env local
```

You land on a shell prompt from the simulated device:

```text
✔  Session opened: sess-local-002
Connected to sim-device-001 (simulated)

sim-device-001:~$ 
```

Run a few commands to verify the session works, then exit:

```bash
sim-device-001:~$ uname -a
sim-device-001:~$ df -h
sim-device-001:~$ exit
```

### Step 7 — Check the local audit log

```bash
stctl remote-access audit list \
  --since 10m \
  --env local
```

Expected output shows the two sessions you opened:

```text
SESSION ID         DEVICE            PROTOCOL     OPENED    DURATION  CLOSED BY
sess-local-001     sim-device-001    diagnostics  14:02:11  00:00:47  user (Ctrl+C)
sess-local-002     sim-device-001    shell        14:03:01  00:01:12  user (exit)
```

### Step 8 — Stop the local stack

```bash
docker compose -f docker-compose.local.yml down
```

---

## Validation

The local stack is working correctly when:

```bash
stctl remote-access probe --env local
# Returns: ✔  Probe session opened and closed successfully

stctl remote-access audit list --since 10m --env local
# Returns session records for sessions you opened
```

---

## Troubleshooting

**`Session broker: unavailable`** after starting the stack
The remote-access-service container may still be starting. Wait 15 seconds and retry. If it persists:

```bash
docker compose -f docker-compose.local.yml logs remote-access-service
```

Look for startup errors in the log output.

**Shell session opens but commands produce no output**
The simulated device echoes commands but has a 500ms artificial latency. Wait a moment after each command. If output never appears, the WebSocket connection dropped — restart the stack.

**`sim-device-001: device not found`**
The simulated device container is not running or has not registered with the broker yet. Check: `docker compose -f docker-compose.local.yml ps simulated-device`. If it shows `exited`, check its logs.

---

## Next steps

Your local remote access development environment is ready.

- [Deploy the Remote Access Service](../deploy-first-iot-service/index.md)
- [Connect a device for remote access](../connect-first-device/index.md)
