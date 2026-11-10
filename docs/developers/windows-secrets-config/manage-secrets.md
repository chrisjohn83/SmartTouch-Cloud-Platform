# Manage secrets safely

## Local development

Use PowerShell environment variables for temporary local values:

```powershell
$env:SMARTTOUCH_API_V2_TOKEN = "demo-token"
$headers = @{ Authorization = "Bearer $env:SMARTTOUCH_API_V2_TOKEN" }
```

Do not save real credentials in Markdown, source code, `.env` files committed to Git, OpenAPI examples, or Deployment API payloads.

## Repository protection

Before committing, inspect staged changes:

```powershell
git diff --cached
```

If a real secret is committed, rotate it immediately and remove it using your organization's incident procedure. Deleting the line in a later commit does not remove the value from Git history.

## Production environments

The reference repository does not implement production secret storage. A production deployment should inject secrets from an approved service such as a cloud secret manager, Kubernetes Secrets with encryption controls, or Vault.

Keep secret values separate from the V2 `configuration` object. Applications should receive them at runtime through the selected secret provider.
