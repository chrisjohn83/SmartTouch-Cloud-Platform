# Submit the deployment

Run this in the same PowerShell terminal where you created `$body`:

```powershell
$headers = @{ Authorization = "Bearer demo-token" }

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8090/v2/services" `
  -Headers $headers `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

A successful request returns status `201` and a service whose status is `healthy`.

## API Playground

1. Open **API Playground → Deployment API → V2**.
2. Authorize with `demo-token`.
3. Open `POST /v2/services`.
4. Paste the JSON request and send it.

Continue to [Verify the deployment](./03-verify-deployment.md).
