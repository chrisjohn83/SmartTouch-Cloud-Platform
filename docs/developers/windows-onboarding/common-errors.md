---
persona: [developer]
task: [troubleshooting, api-testing]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "2.0"
platform-version: "2.x"
tags: [windows, powershell, errors]
---

# Common errors

## Connection refused on port 8090

The API is not running. Start it from `services\platform-api-v2`:

```powershell
$env:SMARTTOUCH_API_V2_TOKEN = "demo-token"
python -m uvicorn app.main:app --reload --port 8090
```

## `401 Unauthorized`

The bearer token is missing or incorrect. Use:

```powershell
$headers = @{ Authorization = "Bearer demo-token" }
```

In the Playground, enter only `demo-token` in the authorization dialog.

## `404 Not Found`

Check both the API version and resource identifier. Valid local examples include:

```text
GET /v2/devices/sensor-001
GET /v2/devices/sensor-002
```

The service root is `http://127.0.0.1:8090/`; V2 endpoints begin with `/v2`.

## Browser CORS error

Open the portal from `http://127.0.0.1:8001`, not from a generated HTML file on disk. The API allows the documented local portal origins.

## Port already in use

Identify the process using the port:

```powershell
Get-NetTCPConnection -LocalPort 8001,8090 -ErrorAction SilentlyContinue |
  Select-Object LocalPort, State, OwningProcess
```

Stop the previous MkDocs or Uvicorn terminal with `Ctrl+C`, then restart it.

## Activation script is blocked

Allow locally created scripts for your user account:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Run the command only if your organization permits this policy change.
