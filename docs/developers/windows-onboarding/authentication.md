---
persona: [developer]
task: [authentication, api-testing]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "2.0"
platform-version: "2.x"
tags: [windows, powershell, bearer-token]
---

# Authenticate to the local API

The V2 reference service uses a development-only bearer token.

## PowerShell

Set the token for the current terminal and create a reusable header:

```powershell
$env:SMARTTOUCH_API_TOKEN = "demo-token"
$headers = @{ Authorization = "Bearer $env:SMARTTOUCH_API_TOKEN" }
```

Verify the token against the Device API:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8090/v2/devices?limit=1" `
  -Headers $headers `
  -Method Get
```

## API Playground

1. Open a V2 Playground page.
2. Select **Authorize**.
3. Enter `demo-token` without the `Bearer` prefix.
4. Apply the credentials and send the request.

## Security boundary

`demo-token` is only for the local sandbox. A deployed environment must use an identity provider or another production authentication mechanism. Never commit real tokens to Git.
