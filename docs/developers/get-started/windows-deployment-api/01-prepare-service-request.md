# Prepare a service request

Create the request body in PowerShell:

```powershell
$deployment = @{
  name = "temperature-service"
  environment = "dev"
  image = "ghcr.io/example/temperature-service:2.0.0"
  replicas = 2
  configuration = @{
    LOG_LEVEL = "info"
    DEVICE_FLEET = "factory-floor"
  }
  dry_run = $false
}

$body = $deployment | ConvertTo-Json -Depth 4
$body
```

Valid environments are `dev`, `staging`, and `prod`. The local sandbox records the image name but does not pull or run the container.

Continue to [Submit the deployment](./02-submit-deployment.md).
