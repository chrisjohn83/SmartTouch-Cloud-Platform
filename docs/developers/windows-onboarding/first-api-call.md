---
persona: [developer]
task: [onboarding, api-testing]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "2.0"
platform-version: "2.x"
tags: [windows, powershell, device-api, api-playground]
---

# Make your first API call

List the devices seeded in the local V2 service.

## PowerShell

```powershell
$headers = @{ Authorization = "Bearer demo-token" }

$response = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8090/v2/devices?limit=10" `
  -Headers $headers `
  -Method Get

$response.data | Format-Table id, display_name, fleet, agent_status
```

Expected devices:

| ID | Fleet | Status |
| --- | --- | --- |
| `sensor-001` | `factory-floor` | `online` |
| `sensor-002` | `factory-floor` | `offline` |

## Filter the list

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8090/v2/devices?status=online&fleet=factory-floor&limit=10" `
  -Headers $headers `
  -Method Get
```

## Get one device

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8090/v2/devices/sensor-001" `
  -Headers $headers `
  -Method Get
```

## Repeat the request in the Playground

1. Open **API Playground → Device API → V2**.
2. Authorize with `demo-token`.
3. Open `GET /v2/devices/{device_id}`.
4. Enter `sensor-001` for `device_id`.
5. Send the request.

Continue to the [Device API V2 Reference](../../api-reference/device-api-v2.md) for the complete contract.
