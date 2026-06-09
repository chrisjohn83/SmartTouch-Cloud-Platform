# Remote Access Sessions API

Sessions represent authenticated tunnels to a device opened through the Remote Access Service.

## List sessions

```text
GET /remote-access/sessions
```

Returns all sessions for the authenticated user. Administrators see sessions for all users.

**Query parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `device_id` | string | No | Filter by device |
| `protocol` | string | No | Filter by protocol: `shell`, `diagnostics`, `file-transfer` |
| `status` | string | No | Filter by status: `open`, `closed` |
| `since` | string | No | ISO 8601 timestamp — return sessions opened after this time |
| `page` | integer | No | Page number (default: `1`) |
| `per_page` | integer | No | Results per page (default: `50`, max: `200`) |

**Sample request:**

```bash
curl -s \
  -H "Authorization: Bearer $(stctl auth token)" \
  "https://api.smarttouch.local/v1/remote-access/sessions?device_id=sensor-001&status=open"
```

**Sample response:**

```json
{
  "status": 200,
  "data": [
    {
      "id": "sess-7f3a1b",
      "device_id": "sensor-001",
      "protocol": "diagnostics",
      "status": "open",
      "user": "alice@example.com",
      "opened_at": "2026-06-08T09:00:00Z",
      "closed_at": null,
      "trace_id": "abc123def456"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 50,
    "total": 1
  }
}
```

---
