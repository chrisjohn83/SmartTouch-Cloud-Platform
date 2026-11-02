"""Runnable SmartTouch Device, Deployment, and Audit Log APIs, version 2."""

from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers import audit, deployments, devices


app = FastAPI(
    title="SmartTouch Platform API v2",
    description=(
        "Runnable reference implementation of the SmartTouch Device, Deployment, "
        "and immutable Audit Log APIs. Use bearer token `demo-token` locally."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    license_info={"name": "Proprietary"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8001",
        "http://localhost:8001",
        "https://chrisjohn83.github.io",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "If-Match", "Idempotency-Key", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or f"req-{uuid4().hex[:16]}"
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


def problem_response(
    request: Request,
    status_code: int,
    title: str,
    detail: str,
    errors: list[dict] | None = None,
    headers: dict | None = None,
) -> JSONResponse:
    body = {
        "type": f"https://docs.smarttouch.io/problems/{status_code}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": request.url.path,
        "request_id": getattr(request.state, "request_id", "unknown"),
    }
    if errors:
        body["errors"] = errors
    return JSONResponse(
        status_code=status_code,
        content=body,
        headers=headers,
        media_type="application/problem+json",
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Content",
        429: "Too Many Requests",
    }
    return problem_response(
        request,
        exc.status_code,
        titles.get(exc.status_code, "Request Failed"),
        str(exc.detail),
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {"location": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
        for error in exc.errors()
    ]
    return problem_response(
        request,
        422,
        "Validation Failed",
        "The request did not satisfy the API contract.",
        errors=errors,
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return problem_response(request, 400, "Bad Request", str(exc))


@app.get("/", tags=["Service"])
def root() -> dict:
    return {
        "service": "SmartTouch Platform API v2",
        "version": "2.0.0",
        "documentation": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health", tags=["Service"])
def health() -> dict:
    return {"status": "UP", "version": "2.0.0"}


app.include_router(devices.router)
app.include_router(deployments.router)
app.include_router(audit.router)
