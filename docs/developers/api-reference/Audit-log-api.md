# Audit Log API

The audit log records all remote access activity. Every session open and close event is written to the audit log with the user identity, device, protocol, and timestamps.

## List audit log entries

```text
GET /audit/remote-access
```

Returns audit log entries for remote access events. Requires administrator role or `audit:read` permission.

**Query parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `device_id` | string | No | Filter by device |
| `user` | string | No | Filter by user email |
| `event` | string | No | Filter by event type: `session.opened`, `session.closed`, `session.expired` |
| `since` | string | No | ISO 8601 timestamp — return entries after this time |
| `until` | string | No | ISO 8601 timestamp — return entries before this time |
| `page` | integer | No | Page number (default: `1`) |
| `per_page` | integer | No | Results per page (default: `100`, max: `500`) |

**Sample request:**

```bash
curl -s \
  -H "Authorization: Bearer $(stctl auth token)" \
  "https://api.smarttouch.local/v1/audit/remote-access?device_id=sensor-001&since=2026-06-08T00:00:00Z"
```

**Sample response:**

```json
{
  "status": 200,
  "data": [
    {
      "id": "audit-001",
      "event": "session.opened",
      "session_id": "sess-9c4d2e",
      "device_id": "sensor-001",
      "protocol": "diagnostics",
      "user": "alice@example.com",
      "source_ip": "10.0.1.42",
      "timestamp": "2026-06-08T09:05:00Z",
      "trace_id": "xyz789abc012"
    },
    {
      "id": "audit-002",
      "event": "session.closed",
      "session_id": "sess-9c4d2e",
      "device_id": "sensor-001",
      "protocol": "diagnostics",
      "user": "alice@example.com",
      "source_ip": "10.0.1.42",
      "timestamp": "2026-06-08T09:18:44Z",
      "trace_id": "xyz789abc012"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 100,
    "total": 2
  }
}
```

---
