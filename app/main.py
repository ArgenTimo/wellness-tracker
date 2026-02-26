"""Wellness Tracker API - FastAPI application entry point."""

import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from app.api.exceptions import generic_exception_handler, validation_exception_handler
from app.api.routes import auth, client, health, links, specialist
from app.core.config import get_settings, settings
from app.core.logging import log_request, setup_logging

setup_logging()

app = FastAPI(
    title="Wellness Tracker API",
    description="Mental wellness tracking system with evidence-first data model",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log request method, path, status and duration."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    user_id = None
    if hasattr(request.state, "user_id"):
        user_id = getattr(request.state, "user_id", None)
    log_request(
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        user_id=user_id,
    )
    return response


# System routes (no prefix)
app.include_router(health.router)

# API v1 routes
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(links.router, prefix=settings.API_V1_PREFIX)
app.include_router(client.router, prefix=settings.API_V1_PREFIX)
app.include_router(client.summary_router, prefix=settings.API_V1_PREFIX)
app.include_router(client.tasks_router, prefix=settings.API_V1_PREFIX)
app.include_router(specialist.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root redirect/info."""
    return {
        "service": "Wellness Tracker API",
        "docs": "/docs",
        "health": "/health",
        "api": settings.API_V1_PREFIX,
    }
