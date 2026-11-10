# SmartTouch Platform API v2

Runnable reference implementation for the SmartTouch Device, Deployment, and Audit Log APIs.

## Run locally

From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:SMARTTOUCH_API_V2_TOKEN = "demo-token"
python -m uvicorn app.main:app --reload --port 8090
```

Open `http://127.0.0.1:8090/docs`, select **Authorize**, and enter `demo-token`.

## REST endpoints

- Device API: `/v2/devices`
- Deployment API: `/v2/services`
- Audit Log API: `/v2/audit/events`
- Health: `/health`
- Combined OpenAPI document: `/openapi.json`

The service uses an in-memory store and seeded sample data. It is suitable for documentation, contract testing, and an API sandbox; replace the store and demonstration bearer-token authentication before production use.

## Tests

```powershell
python -m pytest -q
```

## Export portal OpenAPI specifications

```powershell
python scripts/export_openapi.py
```
