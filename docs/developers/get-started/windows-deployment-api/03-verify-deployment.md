# Verify the deployment

Retrieve the deployment record:

```powershell
$headers = @{ Authorization = "Bearer demo-token" }

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8090/v2/services/temperature-service?environment=dev" `
  -Headers $headers `
  -Method Get
```

List every development service:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8090/v2/services?environment=dev&limit=20" `
  -Headers $headers `
  -Method Get
```

To inspect the seeded example instead, request:

```text
GET /v2/services/remote-access-service?environment=staging
```

The sandbox resets when the API process restarts. Use a database-backed implementation for persistent deployment state.
