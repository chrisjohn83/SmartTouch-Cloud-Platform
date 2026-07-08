"""FastAPI app for SmartTouch AI documentation retrieval."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import load_config
from .retrieval_service import RetrievalServiceError

from .http_api import (
    diagnostics_response,
    handle_answer_context_request,
    handle_answer_request,
    handle_search_request,
    health_response,
)

config = load_config()

app = FastAPI(
    title="SmartTouch AI Docs Retrieval API",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(config.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, Any]:
    return health_response()


@app.get("/diagnostics")
def diagnostics() -> dict:
    return diagnostics_response()


@app.post("/search")
def search(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return handle_search_request(payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RetrievalServiceError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/answer-context")
def answer_context(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return handle_answer_context_request(payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RetrievalServiceError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/answer")
def answer(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return handle_answer_request(payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RetrievalServiceError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
