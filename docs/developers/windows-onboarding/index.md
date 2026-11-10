---
persona: [developer]
task: [onboarding, api-testing]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "2.0"
platform-version: "2.x"
tags: [windows, powershell, onboarding, rest-api]
---

# Developer journey on Windows

Use native PowerShell and the runnable REST API sandbox to learn SmartTouch. The journey does not require WSL2 or `stctl`.

## Journey

1. Confirm the [prerequisites](./prerequisites.md).
2. Review the [platform concepts](./platform-concepts.md).
3. Configure [local authentication](./authentication.md).
4. Make your [first API call](./first-api-call.md).
5. Use [common errors](./common-errors.md) when a request fails.

## What you will use

- PowerShell `Invoke-RestMethod` for command-line API calls
- The V2 API sandbox at `http://127.0.0.1:8090`
- The MkDocs API Playground at `http://127.0.0.1:8001/SmartTouch-Cloud-Platform/`
- Development bearer token `demo-token`

The local service contains seeded Device, Deployment, and Audit Log data. Changes are stored in memory and reset when the API restarts.
