# Register a test device

## PowerShell

```powershell
$headers = @{ Authorization = "Bearer demo-token" }
$body = @{
  id = "sensor-003"
  display_name = "Pressure Sensor 003"
  fleet = "factory-floor"
  agent_version = "2.0.0"
  labels = @{
    site = "pune"
    criticality = "medium"
  }
} | ConvertTo-Json -Depth 4

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8090/v2/devices" `
  -Headers $headers `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

The new device starts with `agent_status` set to `unknown` because the sandbox does not run a physical device agent.

## API Playground

1. Open **API Playground → Device API → V2**.
2. Authorize with `demo-token`.
3. Open `POST /v2/devices`.
4. Paste the JSON equivalent of the PowerShell body.
5. Send the request and confirm status `201`.

Continue to [Inspect device details](./02-inspect-device.md).
