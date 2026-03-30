"""Request logging middleware."""

import time
from typing import Callable
from uuid import uuid4

import structlog
from fastapi import Request, Response

from src.core.logging import get_logger

logger = get_logger(__name__)


async def logging_middleware(
    request: Request,
    call_next: Callable[[Request], Response],
) -> Response:
    """Middleware to log requests and add request context."""
    request_id = str(uuid4())
    start_time = time.perf_counter()
    
    # Bind request context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )
    
    # Add request ID to response headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    # Calculate duration
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    # Log request completion
    logger.info(
        "request_completed",
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2),
    )
    
    return response
