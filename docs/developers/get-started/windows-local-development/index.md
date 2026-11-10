---
persona: [developer]
task: [local-development, api-testing]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "2.0"
platform-version: "2.x"
tags: [windows, powershell, local-development, api-playground]
---

# Set up local development on Windows

This journey uses native Windows PowerShell. It runs the MkDocs portal on port `8001` and the FastAPI V2 sandbox on port `8090`.

You do not need WSL2, Linux, Kubernetes, or `stctl` for the local documentation and API workflows.

## Journey

| Step | Topic | Outcome |
| --- | --- | --- |
| 1 | [Set up Windows API tools](./01-set-up-api-tools.md) | Python, MkDocs, and API dependencies are ready |
| 2 | [Optional Kubernetes access](./02-optional-kubernetes.md) | `kubectl` is ready when a real cluster is available |
| 3 | [Run the portal and API locally](./03-run-portal-and-api.md) | MkDocs and the V2 sandbox run together |

## Local addresses

| Component | Address |
| --- | --- |
| MkDocs portal | `http://127.0.0.1:8001/SmartTouch-Cloud-Platform/` |
| API health | `http://127.0.0.1:8090/health` |
| FastAPI documentation | `http://127.0.0.1:8090/docs` |
| OpenAPI document | `http://127.0.0.1:8090/openapi.json` |

Use bearer token `demo-token` when testing the local V2 APIs.
