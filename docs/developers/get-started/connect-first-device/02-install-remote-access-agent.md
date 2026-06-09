---
persona: [developer]
task: [device-connection, remote-access]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-06"
tags: [remote-access-agent, install, configure, websocket, systemd, agent-yaml]
sequence: 2
part-of: connect-first-device
related:
  - docs/developers/get-started/connect-first-device/01-provision-certificate.md
  - docs/developers/get-started/connect-first-device/03-open-first-remote-session.md

ai-retrieval-questions:
  - "How do I install the Remote Access Agent on a device?"
  - "How do I configure agent.yaml for SmartTouch remote access?"
  - "How does the Remote Access Agent connect to the session broker?"
  - "How do I run the Remote Access Agent as a systemd service?"
  - "What does the Remote Access Agent do?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Install the Remote Access Agent

> **Keyword:** How do I install the Remote Access Agent on a device?
> **Part of:** [Connect a device for remote access](./index.md)—Step 2 of 3

The Remote Access Agent is a lightweight daemon that runs on each device. It opens a single outbound WebSocket connection to the SmartTouch Remote Access Service and holds it open, ready to accept sessions. Because the connection is outbound from the device, sessions work through NAT and corporate firewalls—the device never needs an open inbound port.

---

## Goal

Install the Remote Access Agent on `sensor-001`, configure it with the device certificate from Step 1, and confirm it's connected to the session broker.

---

## Prerequisites

- Completed [Provision a device certificate for remote access](./01-provision-certificate.md)
- `sensor-001.key`, `sensor-001.crt`, and `smarttouch-ca.crt` available on the device
- SSH or physical access to the device
- The device runs Linux (Debian, Ubuntu, 'Raspbian', or Alpine)

---

## How the agent works

---

Device                          SmartTouch Remote Access Service
  │                                         │
  │── outbound WebSocket (TLS) ────────────▶│
  │   (dials on startup, stays open)        │
  │                                         │
  │◀── session request ─────────────────────│ (when a user opens a session)
  │                                         │
  │── session tunnel (bidirectional) ──────▶│◀── 'stctl' / Console (user)

---

The agent doesn't listen on any port. All traffic flows over the single outbound WebSocket. If the connection drops—due to a network interruption or device reboot—the agent reconnects automatically with exponential back-off.

---

## Steps

### Step 1—Generate install instructions

Run this on your development machine. `stctl` generates the exact install commands for your device's operating system and pre-fills them with your device ID and environment's broker address:

```bash
stctl remote-access install-agent \
  --device sensor-001 \
  --env dev \
  --os linux-arm64
```

Replace `linux-arm64` with your device's target: `linux-amd64`, `linux-armv7`, `raspbian`, or `alpine`.

Copy the output—you will run it on the device in Step 3.

### Step 2—Copy certificates to the device

Transfer the three certificate files to the device over a secure channel:

```bash
scp sensor-001.crt  user@device-ip:/etc/smarttouch-agent/device.crt
scp sensor-001.key  user@device-ip:/etc/smarttouch-agent/device.key
scp smarttouch-ca.crt  user@device-ip:/etc/smarttouch-agent/ca.crt
```

On the device, lock down the private key:

```bash
chmod 600 /etc/smarttouch-agent/device.key
chmod 644 /etc/smarttouch-agent/device.crt /etc/smarttouch-agent/ca.crt
```

### Step 3—Run the install commands on the device

SSH into the device and run the four steps from the `stctl` output:

```bash
# Download the agent binary
curl -sSL https://releases.smarttouch.io/agent/latest/linux-arm64/smarttouch-agent \
  -o /usr/local/bin/smarttouch-agent
chmod +x /usr/local/bin/smarttouch-agent
```

```bash
# Create the config directory
mkdir -p /etc/smarttouch-agent
```

```bash
# Write agent.yaml
cat > /etc/smarttouch-agent/agent.yaml << 'AGENT_EOF'
device-id: sensor-001
broker-url: wss://remote-access.dev.smarttouch.io:443
cert: /etc/smarttouch-agent/device.crt
key:  /etc/smarttouch-agent/device.key
ca:   /etc/smarttouch-agent/ca.crt
protocols:
  - shell
  - diagnostics
reconnect-interval: 5s
heartbeat-interval: 30s
AGENT_EOF
```

```bash
# Install as a systemd service and start
smarttouch-agent install --config /etc/smarttouch-agent/agent.yaml
systemctl enable smarttouch-agent
systemctl start smarttouch-agent
```

The `install` command creates a `smarttouch-agent` system user with no login shell and sets correct ownership on `/etc/smarttouch-agent`. This ensures the private key is never accessible to other processes.

### Step 4—Verify the agent is running

On the device:

```bash
systemctl status smarttouch-agent
```

Expected output:

```text
● smarttouch-agent.service — SmartTouch Remote Access Agent
   Active: active (running)

Jun 06 14:03:01 sensor-001 smarttouch-agent[1234]: Connecting to remote-access.dev.smarttouch.io:443
Jun 06 14:03:01 sensor-001 smarttouch-agent[1234]: TLS handshake successful
Jun 06 14:03:01 sensor-001 smarttouch-agent[1234]: Device sensor-001 registered with broker
Jun 06 14:03:01 sensor-001 smarttouch-agent[1234]: Protocols accepted: shell, diagnostics
Jun 06 14:03:01 sensor-001 smarttouch-agent[1234]: Agent ready — waiting for sessions
```

`Agent ready — waiting for sessions` confirms the agent is connected and the broker has accepted the device registration.

### Step 5—Confirm from the platform side

Back on your development machine:

```bash
stctl device status --id sensor-001 --env dev
```

Expected output:

```text
Device ID:      sensor-001
Status:         active
Remote access:  enabled
Agent:          installed, connected
Protocols:      shell, diagnostics
Last seen:      12 seconds ago
Open sessions:  0
```

`Agent: installed, connected` is the confirmation you need. The device is now reachable for remote sessions.

---

## Validation

```bash
# On the device
systemctl is-active smarttouch-agent
# Returns: active

# On your development machine
stctl device status --id sensor-001 --env dev
# Agent: installed, connected
# Last seen: < 60 seconds ago
```

---

## Troubleshooting

**`TLS handshake failed`**

The certificate or CA is mismatched. On the device, verify the certificate chain:

```bash
openssl verify -CAfile /etc/smarttouch-agent/ca.crt /etc/smarttouch-agent/device.crt
# Expected: device.crt: OK
```

If it fails, re-copy `smarttouch-ca.crt` from your development machine— don't use a system CA bundle.

**`device not registered for remote access`**

The device identity was created without the `--remote-access` flag. On your development machine:

```bash
stctl device status --id sensor-001 --env dev
# If Remote access: disabled, recreate the device:
stctl device create --id sensor-001 --remote-access --env dev
```

**`permission denied: /etc/smarttouch-agent/device.key`**

The private key is readable by a user other than `smarttouch-agent`. Fix the ownership:

```bash
chown smarttouch-agent:smarttouch-agent /etc/smarttouch-agent/device.key
chmod 600 /etc/smarttouch-agent/device.key
```

Then restart: `systemctl restart smarttouch-agent`.

**Agent connects but `stctl device status` shows `Agent: not installed`**

The platform can take up to 60 seconds to reflect the connection. Wait and retry. If it still doesn't update, check the broker received the registration:

```bash
stctl logs --env dev --service remote-access-service --since 5m | grep sensor-001
```

---

## Next steps

The Remote Access Agent is installed, connected, and waiting for sessions.

→ Continue to **Step 3:** [Open your first remote access session](./03-open-first-remote-session.md)
