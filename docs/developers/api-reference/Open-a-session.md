# Open a session

```text
POST /remote-access/sessions
```

Opens a new remote access session to a device.

**Request body:**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `device_id` | string | Yes | Target device ID |
| `protocol` | string | Yes | Session protocol: `shell`, `diagnostics`, or `file-transfer` |
| `ttl_seconds` | integer | No | Session time-to-live in seconds (default: `3600`, max: `28800`) |

**Protocol permission requirements:**

| Protocol | Minimum role |
| --- | --- |
| `diagnostics` | developer |
| `shell` | platform-engineer |
| `file-transfer` | administrator |

**Example request:**

```bash
curl -s -X POST \
  -H "Authorization: Bearer $(stctl auth token)" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "sensor-001", "protocol": "diagnostics", "ttl_seconds": 1800}' \
  "https://api.smarttouch.local/v1/remote-access/sessions"
```

**Example response:**

```json
{
  "status": 201,
  "data": {
    "id": "sess-9c4d2e",
    "device_id": "sensor-001",
    "protocol": "diagnostics",
    "status": "open",
    "user": "alice@example.com",
    "opened_at": "2026-06-08T09:05:00Z",
    "expires_at": "2026-06-08T09:35:00Z",
    "websocket_url": "wss://broker.smarttouch.local:8443/sessions/sess-9c4d2e",
    "trace_id": "xyz789abc012"
  }
}
```

Use `websocket_url` to connect your WebSocket client. The `stctl remote-access open` command handles this automatically.

---
