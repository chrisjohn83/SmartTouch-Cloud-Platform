---
persona: [developer]
task: [onboarding, setup]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "2.0"
platform-version: "2.x"
tags: [windows, powershell, prerequisites]
---

# Prerequisites

## Workstation

- Windows 10 or Windows 11
- PowerShell 7 or Windows PowerShell 5.1
- Python 3.12
- Git
- Visual Studio Code

## Repository

Open PowerShell in the repository root:

```powershell
Set-Location "C:\Users\chris\SmartTouch-Cloud-Platform\GitHub\SmartTouch-Cloud-Platform"
```

Confirm the expected branch and Python version:

```powershell
git branch --show-current
python --version
```

## Running services

Complete [Set up local development on Windows](../get-started/windows-local-development/index.md). Then verify:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8090/health"
```

The result must show `status` as `UP` before you use the API Playground.

## Browser

Use a current version of Microsoft Edge, Google Chrome, or Firefox. The portal and API must both be running because the Playground sends requests from port `8001` to port `8090`.
