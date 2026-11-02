# V2 deployment request schema

`POST /v2/services` accepts the following JSON object:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | Yes | Lowercase service name, 3–63 characters |
| `environment` | string | Yes | `dev`, `staging`, or `prod` |
| `image` | string | Yes | Container image reference recorded by the sandbox |
| `replicas` | integer | No | From 1 to 100; defaults to 1 |
| `configuration` | object | No | Non-sensitive string key/value pairs |
| `dry_run` | boolean | No | Validates without saving when `true` |

Example:

```json
{
  "name": "temperature-service",
  "environment": "dev",
  "image": "ghcr.io/example/temperature-service:2.0.0",
  "replicas": 2,
  "configuration": {
    "LOG_LEVEL": "info",
    "DEVICE_FLEET": "factory-floor"
  },
  "dry_run": false
}
```

Use **API Playground → Deployment API → V2** to validate and send the request.
