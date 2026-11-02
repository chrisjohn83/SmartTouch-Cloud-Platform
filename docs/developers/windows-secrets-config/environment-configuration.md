# Configure the local environment

## PowerShell environment variables

Set values for the current terminal session:

```powershell
$env:SMARTTOUCH_API_V2_TOKEN = "demo-token"
$env:SMARTTOUCH_API_BASE_URL = "http://127.0.0.1:8090"
```

Read them without printing the token:

```powershell
$env:SMARTTOUCH_API_BASE_URL
if ($env:SMARTTOUCH_API_V2_TOKEN) { "Token is configured" }
```

Close the terminal to discard session-scoped variables.

## Service configuration

The Deployment API accepts non-sensitive configuration:

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
```

Do not place passwords, tokens, private keys, or connection strings in the `configuration` object.
