# Devices API

Devices are IoT endpoints registered with the platform. Each device has a unique ID, a certificate identity, and an associated Remote Access Agent status.

## List devices

```text
GET /devices
```

Returns all devices visible to the authenticated user.

**Query parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `status` | string | No | Filter by agent status: `online`, `offline`, `unknown` |
| `fleet` | string | No | Filter by fleet label |
| `page` | integer | No | Page number (default: `1`) |
| `per_page` | integer | No | Results per page (default: `50`, max: `200`) |

**Sample request:**

```bash
curl -s \
  -H "Authorization: Bearer $(stctl auth token)" \
  "https://api.smarttouch.local/v1/devices?status=online&per_page=10"
```

**Sample response:**

```json
{
  "status": 200,
  "data": [
    {
      "id": "sensor-001",
      "display_name": "Temperature Sensor 001",
      "fleet": "factory-floor",
      "agent_status": "online",
      "agent_version": "1.4.2",
      "last_seen_at": "2026-06-08T09:12:00Z",
      "certificate": {
        "subject": "CN=sensor-001,OU=remote-access,O=smarttouch",
        "expires_at": "2027-06-08T00:00:00Z"
      }
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 10,
    "total": 1
  }
}
```

---
