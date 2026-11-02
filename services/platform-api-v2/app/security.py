"""Bearer-token authentication for the runnable reference service."""

import os
import secrets
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    subject: str
    roles: tuple[str, ...]


def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Principal:
    expected = os.getenv("SMARTTOUCH_API_V2_TOKEN", "demo-token")
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not secrets.compare_digest(credentials.credentials, expected)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid bearer token is required. Use 'demo-token' for local development.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Principal(subject="developer@smarttouch.local", roles=("developer", "administrator"))
