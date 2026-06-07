---
persona: [developer]
task: [device-connection, remote-access]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-06"
tags: [remote-access, session, shell, diagnostics, audit-log, stctl]
sequence: 3
part-of: connect-first-device
related:
  - docs/developers/get-started/connect-first-device/02-install-remote-access-agent.md
  - docs/developers/get-started/deploy-first-iot-service/index.md

ai-retrieval-questions:
  - "How do I open a remote access session to a device?"
  - "How do I open a shell session to an IoT device?"
  - "How do I open a diagnostics session to a device?"
  - "How do I close a remote access session?"
  - "How do I check the remote access session audit log?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Open your first remote access session

> **Keyword:** How do I open a remote access session to a device?
> **Part of:** [Connect a device for remote access](./index.md) — Step 3 of 3

With the Remote Access Agent running on `sensor-001`, the device is reachable from the platform at any time. This tutorial opens a diagnostics session to inspect the device without a terminal, opens a shell session for direct interaction, and then confirms both sessions appear in the audit log.

---

## Goal

Open a diagnostics session and a shell session to `sensor-001`, understand what each protocol gives you, and confirm the audit log recorded both sessions.

---

## Prerequisites

- Completed [Install the Remote Access Agent](./02-install-remote-access-agent.md)
- `stctl device status --id sensor-001 --env dev` shows `Agent: installed, connected`

---

## Session protocols at a glance

| Protocol | What you get | Who can open it |
|---|---|---|
| `diagnostics` | Read-only stream: CPU, memory, disk, uptime, network, agent version | `developer`, `platform-engineer`, `administrator` |
| `shell` | Interactive terminal on the device | `platform-engineer`, `administrator` |
| `file-transfer` | Secure file upload and download | `administrator` |

Start with `diagnostics` — it gives you a real-time view of device health without any risk of changing device state.

---

## Steps

### Step 1 — Check the device is reachable

```bash
stctl device status --id sensor-001 --env dev
```

Confirm `Agent: installed, connected` and `Open sessions: 0` before proceeding.

### Step 2 — Open a diagnostics session

```bash
stctl remote-access open \
  --device sensor-001 \
  --protocol diagnostics \
  --env dev
```

Expected — a live stream begins immediately:

```text
✔  Session opened
Session ID:  sess-a7c3f1
Device:      sensor-001
Protocol:    diagnostics
Opened by:   alex@example.com
Timeout:     30m  (idle closes after 5m)

━━━ Live Diagnostics — sensor-001 ━━━━━━━━━━━━━━━━━━━━━
  cpu_usage         8%
  memory_used       214 MB / 512 MB
  disk_used         4.1 GB / 16 GB
  uptime            3d 07:42:18
  network_rx        0.4 KB/s
  network_tx        0.1 KB/s
  agent_version     1.4.2
  broker_latency    14 ms
━━━━━━━━━━━━━━━━━━━━━━ refreshes every 5s ━━━━━━━━━━━━━━

Press Ctrl+C to close the session.
```

The stream updates every 5 seconds. `broker_latency` shows the round-trip time from the platform to the device — useful for understanding network quality before opening a shell session.

Press `Ctrl+C` to close.

### Step 3 — Open a shell session

A shell session gives you an interactive terminal on the device. It requires the `platform-engineer` or `administrator` role.

```bash
stctl remote-access open \
  --device sensor-001 \
  --protocol shell \
  --env dev
```

Expected — a shell prompt from the device:

```text
✔  Session opened
Session ID:  sess-b8d4e2
Device:      sensor-001
Protocol:    shell
Note:        This session is recorded in the audit log.

sensor-001:~$
```

You are now in a terminal on the device. The session runs over the same WebSocket tunnel the agent established on startup — no additional ports or network configuration required.

Run a few commands to confirm you have full shell access:

```bash
sensor-001:~$ hostname
sensor-001

sensor-001:~$ systemctl status smarttouch-agent
# Shows the agent service status from the device's perspective

sensor-001:~$ uname -a
# Shows kernel version and architecture

sensor-001:~$ df -h
# Shows disk usage
```

Close the session cleanly:

```bash
sensor-001:~$ exit
```

Typing `exit` closes the session and returns you to your local terminal. The agent remains connected and ready for the next session.

### Step 4 — List sessions opened today

```bash
stctl remote-access list \
  --device sensor-001 \
  --env dev
```

Expected — shows your two closed sessions:

```text
SESSION ID     DEVICE        PROTOCOL     STATUS    OPENED     DURATION
sess-a7c3f1    sensor-001    diagnostics  closed    14:05:22   00:01:03
sess-b8d4e2    sensor-001    shell        closed    14:06:47   00:02:15
```

### Step 5 — Verify the audit log

Every session is written to the tamper-evident audit log. Confirm both sessions were recorded:

```bash
stctl remote-access audit list \
  --device sensor-001 \
  --since 1h \
  --env dev
```

Expected output:

```text
SESSION ID     PROTOCOL     OPENED BY             OPENED     DURATION   CLOSED BY
sess-a7c3f1    diagnostics  alex@example.com      14:05:22   00:01:03   user (Ctrl+C)
sess-b8d4e2    shell        alex@example.com      14:06:47   00:02:15   user (exit)
```

To see the full record of a specific session:

```bash
stctl remote-access audit get --session sess-b8d4e2 --env dev
```

Expected output:

```text
Session ID:    sess-b8d4e2
Device:        sensor-001
Protocol:      shell
Opened by:     alex@example.com  (role: platform-engineer)
Opened at:     2026-06-06T14:06:47Z
Closed at:     2026-06-06T14:09:02Z
Duration:      00:02:15
Closed by:     user (exit command)
Keystroke log: disabled
Broker node:   remote-access-service-6c8d4f-ql7rn
```

Audit records are retained for the period set in the Remote Access Service SSD (`audit.retention: 90d`) and cannot be deleted.

---

## Validation

Remote access is fully working when all three checks pass:

| Check | Command | Expected |
|---|---|---|
| Device reachable | `stctl device status --id sensor-001 --env dev` | `Agent: installed, connected` |
| Session opens | `stctl remote-access open --device sensor-001 --protocol diagnostics --env dev` | Diagnostics stream appears |
| Audit log records session | `stctl remote-access audit list --device sensor-001 --since 1h --env dev` | Session entry present |

---

## Troubleshooting

**`Error: device sensor-001 is not available for sessions`**

The agent has disconnected. Check on the device:

```bash
systemctl status smarttouch-agent
```

If the service has stopped, restart it:

```bash
systemctl restart smarttouch-agent
```

Wait 10 seconds and retry. If the agent keeps stopping, check the logs:

```bash
journalctl -u smarttouch-agent --since "10 minutes ago"
```

**`Error: role insufficient for protocol shell`**

Your account has the `developer` role. Shell sessions require `platform-engineer` or `administrator`. Open a `diagnostics` session instead, or contact your Administrator to request a role upgrade.

**Diagnostics stream opens but shows no data**

The agent's diagnostics module takes up to 10 seconds to collect the first data point. Wait and observe the stream. If no data appears after 15 seconds, check whether the `diagnostics` protocol is listed in `agent.yaml` on the device:

```bash
cat /etc/smarttouch-agent/agent.yaml | grep protocols -A 5
```

If `diagnostics` is missing, add it and restart the agent.

**Shell session opens but commands are slow or unresponsive**

High `broker_latency` in the diagnostics stream (above 500ms) indicates a slow network path between the device and the platform. Commands are transmitted over the same path, so high latency produces a sluggish shell. This is a network condition, not an agent or broker issue.

**Session not appearing in the audit log**

Audit events are written asynchronously — they can take up to 30 seconds to appear after a session closes. Wait and re-run the audit list command.

---

## Summary

`sensor-001` is fully connected for remote access. You can open authenticated diagnostics and shell sessions at any time without network reconfiguration, and every session is captured in the audit log.

---

## Next steps

- [How do I open a remote access session from the SmartTouch console (browser)?](../../deploy-release/how-to-open-remote-session.md)
- [How do I set up alerts when a session is opened?](../../observability/how-to-session-alerts.md)
- [How do I manage sessions across multiple devices?](../../secrets-config/how-to-manage-sessions.md)
- [How do I export the audit log for compliance reporting?](../../observability/how-to-export-audit-log.md)
