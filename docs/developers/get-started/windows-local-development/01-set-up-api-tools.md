---
persona: [developer]
task: [local-development, api-testing]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "2.0"
platform-version: "2.x"
tags: [windows, powershell, api, setup]
sequence: 1
part-of: windows-local-development
---

# Set up Windows API tools

Prepare a native Windows PowerShell environment for the SmartTouch documentation portal and runnable V2 API sandbox. WSL2 and the unavailable `stctl` CLI are not required.

## Prerequisites

- Windows 10 or Windows 11
- PowerShell 7 or Windows PowerShell 5.1
- Python 3.12
- Git
- Visual Studio Code

## 1. Open the repository

```powershell
Set-Location "C:\Users\chris\SmartTouch-Cloud-Platform\GitHub\SmartTouch-Cloud-Platform"
```

## 2. Create and activate the virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If the prompt already begins with `(.venv)`, the environment is active and you can skip this step.

## 3. Install the API and documentation tools

```powershell
python -m pip install -r .\services\platform-api-v2\requirements.txt
python -m pip install mkdocs mkdocs-material pymdown-extensions
```

## 4. Verify the tools

```powershell
python --version
mkdocs --version
```

## 5. Configure the local API token

The reference service accepts this development-only bearer token:

```powershell
$env:SMARTTOUCH_API_V2_TOKEN = "demo-token"
```

The value applies only to the current PowerShell session. Do not use this token for a production service.

Continue to [Run the portal and API locally](./03-run-portal-and-api.md).
