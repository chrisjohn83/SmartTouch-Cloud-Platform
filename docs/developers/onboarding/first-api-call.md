---
persona: [developer]
task: [getting-started, remote-access, authentication]
product: [smarttouch-cloud]
validation: automation
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
tags: [onboarding, first-api-call, remote-access, tutorial, stctl, rest-api, session]
related:
  - docs/developers/onboarding/authentication.md
  - docs/developers/onboarding/common-errors.md
  - docs/developers/api-reference/rest-api.md
  - docs/developers/api-reference/stctl-cli-reference.md
ai-retrieval-questions:
  - "How do I make my first API call to SmartTouch?"
  - "How do I open a remote access session using the REST API?"
  - "How do I find a device and open a session?"
  - "What is the sequence for opening a remote access session?"
  - "How do I confirm a remote access session is open?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# First API call

> **Keyword:** How do I make my first API call to SmartTouch?

This tutorial walks you through the complete journey from authenticated user to successfully opened and closed remote access session. Each step shows both the `stctl` CLI command and the equivalent REST API call with `curl`.

**Estimated time:** 20 minutes

---

## Before you start

Confirm these items are ready:

- `stctl` is installed and `stctl version` returns output
- You are authenticated — `stctl auth status` shows `Token: valid`
- A device ID is available (physical device or simulator — see [Prerequisites](./prerequisites.md))
- Your bearer token is stored in `$TOKEN`:

  ```bash
  TOKEN=$(stctl auth token)
  echo $TOKEN   # must print a JWT string, not be empty
  ```

If any of these are not ready, complete [Authentication](./authentication.md) first.

---

## The journey at a glance

---

Step 1 → Get credentials        (done in Authentication)

Step 2 → Generate a token       (confirm $TOKEN is set)

Step 3 → Find a device          (GET /devices)

Step 4 → Verify device online   (GET /devices/{id}/agent-status)

Step 5 → Open a session         (POST /remote-access/sessions)

Step 6 → Confirm success        (GET /remote-access/sessions/{id})

Step 7 → Close the session      (DELETE /remote-access/sessions/{id})

---

---

## Step 1—Get credentials

**Status: complete.** You completed this in [Authentication](./authentication.md). Your credentials are stored in `~/.stctl/credentials`.

If you need to re-authenticate:

```bash
stctl auth login
```

---

## Step 2—Generate a token

Refresh your bearer token and store it in `$TOKEN`. Do this at the start of any new terminal session.

**stctl:**

```bash
TOKEN=$(stctl auth token)
```

**Verify:**

```bash
stctl auth status
```

Expected output:

```text

User:   alice@example.com

Token:  valid (expires in 7h 55m)

Role:   developer
```

**REST API equivalent:**

There is no `/token` endpoint — token generation is handled by `stctl` using your SSO credentials. For non-interactive use, ask your Administrator for a service account token and assign it directly:

```bash
export TOKEN=<service-account-token>
```

---

## Step 3—Find a device

List the devices registered on the platform to find one you can connect to.

**stctl:**

```bash
stctl device list --env dev
```

Expected output:

```text
ID                       DISPLAY NAME              FLEET           AGENT STATUS   LAST SEEN

onboarding-device-01     Onboarding Device 01      —               online         1m ago

sensor-001               Temperature Sensor 001   factory-floor   online         4m ago

sensor-002               Humidity Sensor 002      factory-floor   offline        2h ago
```

Choose a device with `AGENT STATUS: online`. Use its ID in the steps below — this guide uses `onboarding-device-01`.

**REST API equivalent:**

```bash
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/devices?status=online"
```

Expected response:

```json
{
  "status": 200,
  "data": [
    {
      "id": "onboarding-device-01",
      "display_name": "Onboarding Device 01",
      "fleet": null,
      "agent_status": "online",
      "agent_version": "1.4.2",
      "last_seen_at": "2026-06-08T09:12:00Z"
    }
  ],
  "meta": { "page": 1, "per_page": 50, "total": 1 }
}
```

**If no devices are listed:** Start the simulator — see [Prerequisites](./prerequisites.md).

---

## Step 4—Verify the device is online

Before opening a session, confirm the Remote Access Agent on the device is connected and responsive.

**stctl:**

```bash
stctl device agent-status onboarding-device-01
```

Expected output:

```text
Device:        onboarding-device-01
Agent status:  online
Connected at:  2026-06-08 09:05:32 UTC
Broker:        wss://broker.smarttouch.local:8443
Latency:       12ms
```

**REST API equivalent:**

```bash
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/devices/onboarding-device-01/agent-status"
```

Expected response:

```json
{
  "status": 200,
  "data": {
    "device_id": "onboarding-device-01",
    "agent_status": "online",
    "connected_at": "2026-06-08T09:05:32Z",
    "broker_url": "wss://broker.smarttouch.local:8443",
    "latency_ms": 12
  }
}
```

**If `agent_status` is `offline`:** The device agent is not connected. See [Why is my device not connecting?](../troubleshooting/why-device-not-connecting.md) before proceeding.

---

## Step 5—Open a session

Open a `diagnostics` session to the device. The `diagnostics` protocol allows read-only inspection and is available to all developers.

**stctl (interactive):**

```bash
stctl remote-access open onboarding-device-01 \
  --protocol diagnostics \
  --ttl 30m
```

Expected output:

```text
Opening diagnostics session to onboarding-device-01...
Session ID:   sess-7f3a1b
Protocol:     diagnostics
Expires at:   2026-06-08 09:45:00 UTC

Connected. Type 'exit' to close the session.
[onboarding-device-01 diagnostics]$
```

You are now connected to the device. The `[onboarding-device-01 diagnostics]$` prompt confirms the session is active.

**stctl (non-interactive, returns session metadata):**

```bash
stctl remote-access open onboarding-device-01 \
  --protocol diagnostics \
  --ttl 30m \
  --output json
```

**REST API equivalent:**

```bash
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "onboarding-device-01",
    "protocol": "diagnostics",
    "ttl_seconds": 1800
  }' \
  "https://api.smarttouch.local/v1/remote-access/sessions"
```

Expected response:

```json
{
  "status": 201,
  "data": {
    "id": "sess-7f3a1b",
    "device_id": "onboarding-device-01",
    "protocol": "diagnostics",
    "status": "open",
    "user": "alice@example.com",
    "opened_at": "2026-06-08T09:15:00Z",
    "expires_at": "2026-06-08T09:45:00Z",
    "websocket_url": "wss://broker.smarttouch.local:8443/sessions/sess-7f3a1b",
    "trace_id": "abc123def456"
  }
}
```

Save the session ID for the next steps:

```bash
SESSION_ID="sess-7f3a1b"
```

---

## Step 6 — Confirm success

Verify the session is open and active.

**stctl:**

```bash
stctl remote-access list \
  --device onboarding-device-01 \
  --status open
```

Expected output:

```text
SESSION ID   DEVICE                  PROTOCOL      STATUS   USER                   OPENED
sess-7f3a1b  onboarding-device-01   diagnostics   open     alice@example.com      2m ago
```

**REST API equivalent:**

```bash
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/remote-access/sessions/$SESSION_ID"
```

Expected response:

```json
{
  "status": 200,
  "data": {
    "id": "sess-7f3a1b",
    "device_id": "onboarding-device-01",
    "protocol": "diagnostics",
    "status": "open",
    "user": "alice@example.com",
    "opened_at": "2026-06-08T09:15:00Z",
    "expires_at": "2026-06-08T09:45:00Z",
    "closed_at": null,
    "bytes_sent": 128,
    "bytes_received": 64,
    "trace_id": "abc123def456"
  }
}
```

`"status": "open"` and `"closed_at": null` confirm the session is active.

**Check the audit log** to confirm the session appears in the platform audit trail:

```bash
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/audit/remote-access?device_id=onboarding-device-01"
```

Expected response includes a `session.opened` event:

```json
{
  "status": 200,
  "data": [
    {
      "id": "audit-001",
      "event": "session.opened",
      "session_id": "sess-7f3a1b",
      "device_id": "onboarding-device-01",
      "protocol": "diagnostics",
      "user": "alice@example.com",
      "timestamp": "2026-06-08T09:15:00Z",
      "trace_id": "abc123def456"
    }
  ]
}
```

---

## Step 7—Close the session

Close the session when you are finished. Sessions expire automatically after their TTL, but closing them explicitly is best practice — it frees the protocol slot on the device immediately and creates a clean audit record.

**stctl:**

```bash
stctl remote-access close sess-7f3a1b
```

Expected output:

```text
Session sess-7f3a1b closed.
```

**REST API equivalent:**

```bash
curl -s -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/remote-access/sessions/$SESSION_ID"
```

Expected response:

```json
{
  "status": 200,
  "data": {
    "id": "sess-7f3a1b",
    "status": "closed",
    "closed_at": "2026-06-08T09:28:44Z"
  }
}
```

**Verify the session is closed:**

```bash
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/remote-access/sessions/$SESSION_ID"
```

Expected response shows `"status": "closed"` and a `closed_at` timestamp.

**Verify the audit log records the close event:**

```bash
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/audit/remote-access?device_id=onboarding-device-01"
```

Expected response now includes a `session.closed` event:

```json
{
  "data": [
    {
      "event": "session.closed",
      "session_id": "sess-7f3a1b",
      "timestamp": "2026-06-08T09:28:44Z"
    },
    {
      "event": "session.opened",
      "session_id": "sess-7f3a1b",
      "timestamp": "2026-06-08T09:15:00Z"
    }
  ]
}
```

---

## Journey complete

You have successfully:

1. Authenticated and generated a bearer token
2. Listed devices and identified an online device
3. Verified the device agent is connected
4. Opened a `diagnostics` session using both `stctl` and the REST API
5. Confirmed the session was active and visible in the audit log
6. Closed the session and verified the close event in the audit log

---

## Quick reference card

Save these commands for daily use:

```bash
# Refresh token
TOKEN=$(stctl auth token)

# List online devices
stctl device list --status online --env dev

# Check agent status
stctl device agent-status <device_id>

# Open a diagnostics session
stctl remote-access open <device_id> --protocol diagnostics

# List open sessions
stctl remote-access list --status open

# Close a session
stctl remote-access close <session_id>
```

REST API equivalents:

```bash
# List online devices
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/devices?status=online"

# Check agent status
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/devices/<device_id>/agent-status"

# Open a session
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"device_id":"<device_id>","protocol":"diagnostics","ttl_seconds":1800}' \
  "https://api.smarttouch.local/v1/remote-access/sessions"

# Get session status
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/remote-access/sessions/<session_id>"

# Close a session
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/remote-access/sessions/<session_id>"

# Audit log
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/audit/remote-access?device_id=<device_id>"
```

---

## If something went wrong

See [Common errors](./common-errors.md) for a reference to every error you may have encountered during this journey.

---

## Next steps

| What to do next | Link |
| --- | --- |
| Connect a real physical device | [Connect a device for remote access](../get-started/connect-first-device/index.md) |
| Deploy your first IoT service | [How do I deploy a service?](../deploy-release/how-to-deploy-service.md) |

<!-- | See all REST API endpoints | [SmartTouch REST API reference](../api-reference/index.md) | -->

<!--| See all stctl commands | [stctl CLI reference](../api-reference/stctl-cli-reference.md) -->
