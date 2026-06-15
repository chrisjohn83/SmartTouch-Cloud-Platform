---
persona: [developer]
task: [troubleshooting, getting-started, remote-access, authentication]
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
tags: [onboarding, errors, troubleshooting, api, authentication, remote-access, reference]
related:
  - docs/developers/onboarding/first-api-call.md
  - docs/developers/onboarding/authentication.md
  - docs/developers/troubleshooting/why-device-not-connecting.md
  - docs/developers/api-reference/rest-api.md
ai-retrieval-questions:
  - "What does 401 unauthorized mean in SmartTouch?"
  - "What does 403 forbidden mean in SmartTouch?"
  - "Why am I getting a conflict error when opening a session?"
  - "What does 422 unprocessable entity mean for a remote access session?"
  - "What errors will I encounter during SmartTouch onboarding?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Common errors

> **Keyword:** What errors will I encounter during SmartTouch onboarding?

This reference covers every error you are likely to encounter while working through the [First API call](./first-api-call.md) journey and during normal development. Each entry includes the HTTP status code (for REST API calls), the error message, the cause, and the fix.

---

## Quick lookup table

| HTTP status | Error code | Where it occurs | Go to |
| --- | --- | --- | --- |
| 401 | `unauthorized` | Any API call | [401 Unauthorized](#401-unauthorized) |
| 403 | `forbidden` | Opening a session | [403 Forbidden](#403-forbidden) |
| 404 | `not_found` | Get device, get session | [404 Not Found](#404-not-found) |
| 409 | `conflict` | Opening a session | [409 Conflict](#409-conflict) |
| 422 | `unprocessable_entity` | Opening a session | [422 Unprocessable Entity](#422-unprocessable-entity) |
| 429 | `rate_limited` | Any API call | [429 Rate Limited](#429-rate-limited) |
| 500 | `internal_error` | Any API call | [500 Internal Error](#500-internal-error) |
| — | stctl errors | CLI commands | [stctl errors](#stctl-errors) |

---

## 401 Unauthorized

**HTTP status:** 401

**Response body:**

```json
{
  "error": "unauthorized",
  "message": "Bearer token is missing or has expired.",
  "status": 401
}
```

**Occurs at:** Every API endpoint when the `Authorization` header is missing, malformed, or contains an expired token.

**Causes and fixes:**

| Cause | Fix |
| --- | --- |
| `$TOKEN` variable is empty | Run `TOKEN=$(stctl auth token)` and verify `echo $TOKEN` prints a value |
| Token has expired (8-hour lifetime) | Run `TOKEN=$(stctl auth token)` to refresh |
| `Authorization` header typo | Confirm the header is exactly `Authorization: Bearer <token>` with a capital A and a space between `Bearer` and the token |
| Service account token was revoked | Ask your Administrator to issue a new service account token |

**Example fix:**

```bash
# Re-export a fresh token
TOKEN=$(stctl auth token)

# Retry the failed request
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/devices"
```

---

## 403 Forbidden

**HTTP status:** 403

**Response body:**

```json
{
  "error": "forbidden",
  "message": "Your role does not permit shell sessions. Required role: platform-engineer.",
  "status": 403
}
```

**Occurs at:** `POST /remote-access/sessions` when the authenticated user's role does not meet the minimum requirement for the requested protocol.

**Protocol role requirements:**

| Protocol | Minimum role |
| --- | --- |
| `diagnostics` | developer |
| `shell` | platform-engineer |
| `file-transfer` | administrator |

**Causes and fixes:**

| Cause | Fix |
| --- | --- |
| Requesting `shell` with a `developer` role | Use `"protocol": "diagnostics"` instead, or ask a Platform Engineer to open the `shell` session |
| Requesting `file-transfer` with a `developer` role | Ask an Administrator to perform the file transfer |
| Account role not yet assigned | Ask your Administrator to assign the correct role |

**Verify your current role:**

```bash
stctl auth status
```

---

## 404 Not Found

**HTTP status:** 404

**Response body:**

```json
{
  "error": "not_found",
  "message": "Device not found: onboarding-device-99",
  "status": 404
}
```

**Occurs at:** `GET /devices/{id}`, `GET /devices/{id}/agent-status`, `POST /remote-access/sessions`.

**Causes and fixes:**

| Cause | Fix |
| --- | --- |
| Device ID is misspelled | Run `stctl device list` to see the exact registered IDs |
| Device has never connected to the platform | Provision the device and install the Remote Access Agent — see [Connect a device for remote access](../get-started/connect-first-device/index.md) |
| Device was deleted from the platform | Ask your Administrator to re-register the device |
| Simulator is not running | Run `stctl simulator start --device-id onboarding-device-01 --remote-access` |

**Find the correct device ID:**

```bash
stctl device list --env dev
```

---

## 409 Conflict

**HTTP status:** 409

**Response body:**

```json
{
  "error": "conflict",
  "message": "A diagnostics session is already open for device onboarding-device-01.",
  "status": 409
}
```

**Occurs at:** `POST /remote-access/sessions`.

**Cause:** Only one session per protocol per device can be open at a time. A session was opened earlier and not closed.

**Fix:** List open sessions, find the existing session, and close it before opening a new one.

```bash
# List open sessions for the device
stctl remote-access list --device onboarding-device-01 --status open

# Close the existing session
stctl remote-access close <session_id>

# Retry opening a new session
stctl remote-access open onboarding-device-01 --protocol diagnostics
```

**REST API equivalent:**

```bash
# List open sessions
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/remote-access/sessions?device_id=onboarding-device-01&status=open"

# Close the existing session
curl -s -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/remote-access/sessions/<session_id>"
```

---

## 422 Unprocessable Entity

**HTTP status:** 422

**Response body:**

```json
{
  "error": "unprocessable_entity",
  "message": "Cannot open session: device agent is offline.",
  "status": 422
}
```

**Occurs at:** `POST /remote-access/sessions`.

**Cause:** The request is valid but cannot be completed because the device agent is not connected to the session broker. The device appears in the platform but is not reachable.

**Fix:**

1. Verify the agent status:

   ```bash
   stctl device agent-status onboarding-device-01
   ```

2. If `agent_status` is `offline`, check whether the agent process is running on the device:

   ```bash
   # On the device
   systemctl status smarttouch-agent
   ```

3. If the agent is stopped, start it:

   ```bash
   # On the device
   systemctl start smarttouch-agent
   ```

4. Wait 15 seconds, then check agent status again:

   ```bash
   stctl device agent-status onboarding-device-01
   ```

5. Retry opening the session once `agent_status` returns `online`.

For detailed device connection troubleshooting, see [Why is my device not connecting?](../troubleshooting/why-device-not-connecting.md).

---

## 429 Rate Limited

**HTTP status:** 429

**Response body:**

```json
{
  "error": "rate_limited",
  "message": "Too many requests. Retry after 42 seconds.",
  "status": 429
}
```

**Response header:** `Retry-After: 42`

**Occurs at:** Any API endpoint when the rate limit for that endpoint group is exceeded.

**Rate limits:**

| Endpoint group | Limit |
| --- | --- |
| `GET /devices` | 120 requests per minute |
| `POST /remote-access/sessions` | 30 requests per minute |
| `GET /audit/remote-access` | 60 requests per minute |

**Fix:** Wait the number of seconds in the `Retry-After` header before retrying.

In scripts, implement exponential backoff:

```bash
# Simple retry with backoff
RETRY_AFTER=$(curl -sI \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/devices" \
  | grep -i "retry-after" | awk '{print $2}' | tr -d '\r')

sleep ${RETRY_AFTER:-5}
```

Rate limits apply per user, not per device. If you are scripting many session opens in quick succession, add a `sleep 2` between calls.

---

## 500 Internal Error

**HTTP status:** 500

**Response body:**

```json
{
  "error": "internal_error",
  "message": "An internal error occurred. Request ID: req-abc123.",
  "status": 500
}
```

**Occurs at:** Any API endpoint.

**Cause:** An unexpected error in the SmartTouch platform itself.

**Fix:**

1. Check the platform status page or run `stctl status --env dev`.
2. If the platform is healthy, retry the request after 30 seconds — the error may be transient.
3. If the error persists, contact your Platform Engineer with the `Request ID` from the response body.

---

## stctl errors

### `stctl: command not found`

`stctl` is not installed or not on your `PATH`. See [Prerequisites](./prerequisites.md) for installation instructions.

---

### `Error: authentication required`

You are not logged in. Run:

```bash
stctl auth login
```

---

### `Error: device not found: <device_id>`

The device ID does not exist or was mistyped. Run `stctl device list` to see registered device IDs.

---

### `Error: session already open for protocol diagnostics`

Equivalent to HTTP 409 Conflict. List and close the existing session:

```bash
stctl remote-access list --device <device_id> --status open
stctl remote-access close <session_id>
```

---

### `Error: forbidden — your role does not permit shell sessions`

Equivalent to HTTP 403. Use `--protocol diagnostics` or contact your Platform Engineer.

---

### `Error: context deadline exceeded`

The request timed out. This usually means the platform API is not reachable from your network. Verify your network can reach the API endpoint:

```bash
curl -s "https://api.smarttouch.local/v1/devices" --max-time 5
```

If this fails, check your VPN connection or ask your Platform Engineer to confirm the platform URL.

---

## Error handling in scripts

When calling the REST API from scripts, check the HTTP status code before processing the response body:

```bash
HTTP_STATUS=$(curl -s -o /tmp/response.json -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/devices/onboarding-device-01/agent-status")

if [ "$HTTP_STATUS" -ne 200 ]; then
  echo "Error $HTTP_STATUS:"
  cat /tmp/response.json
  exit 1
fi

cat /tmp/response.json
```

---

## Related

- [First API call](./first-api-call.md)
- [Authentication](./authentication.md)
- [Why is my device not connecting?](../troubleshooting/why-device-not-connecting.md)
- [SmartTouch REST API reference — Error codes](../api-reference/Device-api.md)
