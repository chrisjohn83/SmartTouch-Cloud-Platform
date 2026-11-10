# Inspect device details

List the available devices:

```powershell
$headers = @{ Authorization = "Bearer demo-token" }

$response = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8090/v2/devices?fleet=factory-floor&limit=10" `
  -Headers $headers `
  -Method Get

$response.data | Format-Table id, display_name, agent_status, agent_version
```

Retrieve the device registered in the previous step:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8090/v2/devices/sensor-003" `
  -Headers $headers `
  -Method Get
```

Use `sensor-001` if you restarted the API and the custom device is no longer present.

## Physical device boundary

The local service simulates registry data only. Installing a real remote-access agent, provisioning certificates, and managing a Linux device service are outside the local Windows sandbox.

Continue to [Verify agent status](./03-verify-agent-status.md).
