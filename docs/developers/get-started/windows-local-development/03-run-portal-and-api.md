---
persona: [developer]
task: [local-development, api-testing]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "2.0"
platform-version: "2.x"
tags: [windows, powershell, fastapi, mkdocs, api-playground]
sequence: 3
part-of: windows-local-development
---

# Run the portal and API locally

Run the API and MkDocs in two PowerShell terminals.

## Terminal 1: start the V2 API

```powershell
Set-Location "C:\Users\chris\SmartTouch-Cloud-Platform\GitHub\SmartTouch-Cloud-Platform"
.\.venv\Scripts\Activate.ps1
$env:SMARTTOUCH_API_V2_TOKEN = "demo-token"
Set-Location .\services\platform-api-v2
python -m uvicorn app.main:app --reload --port 8090
```

Keep this terminal running. Verify the service from another terminal:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8090/health"
```

## Terminal 2: start MkDocs

```powershell
Set-Location "C:\Users\chris\SmartTouch-Cloud-Platform\GitHub\SmartTouch-Cloud-Platform"
.\.venv\Scripts\Activate.ps1
mkdocs serve --dev-addr 127.0.0.1:8001
```

Open `http://127.0.0.1:8001/SmartTouch-Cloud-Platform/`.

## Test the Device API from PowerShell

```powershell
$headers = @{ Authorization = "Bearer demo-token" }

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8090/v2/devices?limit=10" `
  -Headers $headers `
  -Method Get
```

## Test from the portal

1. Open **API Playground → Device API → V2**.
2. Select **Authorize** and enter `demo-token`.
3. Open `GET /v2/devices`.
4. Set `limit` to `10` and send the request.

The response contains the seeded devices `sensor-001` and `sensor-002`.

## Stop the services

Press `Ctrl+C` in each server terminal. Then deactivate the Python environment:

```powershell
deactivate
```
