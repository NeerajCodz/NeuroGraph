"""Error handling middleware."""

from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from src.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    MemoryAccessDeniedError,
    MemoryConflictError,
    MemoryNotFoundError,
    NeuroGraphError,
    RateLimitError,
    ValidationError,
)
from src.core.logging import get_logger

logger = get_logger(__name__)


async def error_handler_middleware(
    request: Request,
    call_next: Callable[[Request], Response],
) -> Response:
    """Middleware to handle exceptions and return appropriate HTTP responses."""
    try:
        return await call_next(request)
    except MemoryNotFoundError as e:
        logger.warning("memory_not_found", error=e.message, path=request.url.path)
        return JSONResponse(
            status_code=404,
            content={"detail": e.message, "error_type": "not_found"},
        )
    except MemoryAccessDeniedError as e:
        logger.warning("access_denied", error=e.message, path=request.url.path)
        return JSONResponse(
            status_code=403,
            content={"detail": e.message, "error_type": "access_denied"},
        )
    except MemoryConflictError as e:
        logger.warning("conflict", error=e.message, path=request.url.path)
        return JSONResponse(
            status_code=409,
            content={"detail": e.message, "error_type": "conflict"},
        )
    except AuthenticationError as e:
        logger.warning("authentication_failed", error=e.message, path=request.url.path)
        return JSONResponse(
            status_code=401,
            content={"detail": e.message, "error_type": "authentication_error"},
        )
    except AuthorizationError as e:
        logger.warning("authorization_failed", error=e.message, path=request.url.path)
        return JSONResponse(
            status_code=403,
            content={"detail": e.message, "error_type": "authorization_error"},
        )
    except ValidationError as e:
        logger.warning("validation_failed", error=e.message, path=request.url.path)
        return JSONResponse(
            status_code=422,
            content={"detail": e.message, "error_type": "validation_error"},
        )
    except RateLimitError as e:
        logger.warning("rate_limited", error=e.message, path=request.url.path)
        return JSONResponse(
            status_code=429,
            content={"detail": e.message, "error_type": "rate_limit"},
        )
    except NeuroGraphError as e:
        logger.error("neurograph_error", error=e.message, details=e.details, path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": e.message, "error_type": "server_error"},
        )
    except Exception as e:
        logger.exception("unhandled_error", error=str(e), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error_type": "server_error"},
        )
