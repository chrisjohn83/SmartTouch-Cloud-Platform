# Get a device

```text
GET /devices/{device_id}
```

Returns details for a single device.

**Path parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `device_id` | string | Yes | Unique device identifier |

**Sample request:**

```bash
curl -s \
  -H "Authorization: Bearer $(stctl auth token)" \
  "https://api.smarttouch.local/v1/devices/sensor-001"
```

**Sample response:**

```json
{
  "status": 200,
  "data": {
    "id": "sensor-001",
    "display_name": "Temperature Sensor 001",
    "fleet": "factory-floor",
    "agent_status": "online",
    "agent_version": "1.4.2",
    "last_seen_at": "2026-06-08T09:12:00Z",
    "remote_access": {
      "enabled": true,
      "broker_url": "wss://broker.smarttouch.local:8443",
      "allowed_protocols": ["shell", "diagnostics"]
    },
    "certificate": {
      "subject": "CN=sensor-001,OU=remote-access,O=smarttouch",
      "serial": "4a:f3:...",
      "issued_at": "2026-06-08T00:00:00Z",
      "expires_at": "2027-06-08T00:00:00Z"
    }
  }
}
```

---
