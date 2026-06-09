# Get a session

```text
GET /remote-access/sessions/{session_id}
```

Returns details for a single session, including its current status and trace ID.

**Sample response:**

```json
{
  "status": 200,
  "data": {
    "id": "sess-9c4d2e",
    "device_id": "sensor-001",
    "protocol": "diagnostics",
    "status": "open",
    "user": "alice@example.com",
    "opened_at": "2026-06-08T09:05:00Z",
    "expires_at": "2026-06-08T09:35:00Z",
    "closed_at": null,
    "bytes_sent": 4096,
    "bytes_received": 2048,
    "trace_id": "xyz789abc012"
  }
}
```

---
