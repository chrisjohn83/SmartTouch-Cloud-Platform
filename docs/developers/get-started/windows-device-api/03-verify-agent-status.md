# Verify device agent status

Use the seeded online device for a positive test:

```powershell
$headers = @{ Authorization = "Bearer demo-token" }

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8090/v2/devices/sensor-001/agent-status" `
  -Headers $headers `
  -Method Get
```

Expected values include:

```text
device_id    : sensor-001
agent_status : online
latency_ms   : 12
```

Other useful tests:

- `sensor-002` returns `offline`.
- A newly registered `sensor-003` returns `unknown`.
- `sensor-999` returns `404 Not Found`.

You can send the same requests from **API Playground → Device API → V2**.
