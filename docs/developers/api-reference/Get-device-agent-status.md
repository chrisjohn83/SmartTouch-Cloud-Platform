# Get device agent status

```text
GET /devices/{device_id}/agent-status
```

Returns the current connection state of the Remote Access Agent on a device.

**Sample response:**

```json
{
  "status": 200,
  "data": {
    "device_id": "sensor-001",
    "agent_status": "online",
    "connected_at": "2026-06-08T08:55:32Z",
    "broker_url": "wss://broker.smarttouch.local:8443",
    "latency_ms": 12
  }
}
```

---
