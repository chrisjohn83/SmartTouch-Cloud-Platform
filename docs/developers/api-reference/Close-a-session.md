# Close a session

```text
DELETE /remote-access/sessions/{session_id}
```

Closes an open session immediately. The device agent terminates the tunnel within 5 seconds.

**Sample request:**

```bash
curl -s -X DELETE \
  -H "Authorization: Bearer $(stctl auth token)" \
  "https://api.smarttouch.local/v1/remote-access/sessions/sess-9c4d2e"
```

**Sample response:**

```json
{
  "status": 200,
  "data": {
    "id": "sess-9c4d2e",
    "status": "closed",
    "closed_at": "2026-06-08T09:18:44Z"
  }
}
```

---
