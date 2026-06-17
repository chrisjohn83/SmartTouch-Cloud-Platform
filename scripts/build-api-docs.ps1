$apis = @(
    "device-api",
    "session-api",
    "deployment-api",
    "remote-access-api",
    "audit-log-api"
)

foreach ($api in $apis)
{
    Write-Host "Building $api..."

    npx @redocly/cli build-docs `
        "docs/openapi/$api.yaml" `
        -o "site/apis/$api.html"

    if ($LASTEXITCODE -ne 0)
    {
        Write-Host "FAILED: $api"
        exit 1
    }

    Write-Host "SUCCESS: $api"
}

Write-Host ""
Write-Host "Generated Files"
