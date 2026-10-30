"""Small HTTP helper with retry/backoff for rate limits and transient errors."""
from __future__ import annotations

import os
import time

import requests


def env(name: str, required: bool = True) -> str | None:
    val = os.environ.get(name)
    if required and not val:
        raise SystemExit(f"Missing environment variable {name}")
    return val


def request(session: requests.Session, url: str, *, method: str = "GET", params=None,
            json_body=None, retries: int = 4) -> requests.Response:
    for attempt in range(retries):
        r = session.request(method, url, params=params, json=json_body, timeout=30)
        if r.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
            wait = int(r.headers.get("Retry-After", 2 ** attempt))
            time.sleep(min(wait, 60))
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()
    return r
