"""FastAPI main application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from src.api.middleware.error_handler import error_handler_middleware
from src.api.middleware.logging import logging_middleware
from src.api.routes import api_router
from src.mcp.http_transport import router as mcp_router
from src.core.config import get_settings
from src.core.logging import get_logger, setup_logging
from src.db.neo4j import get_neo4j_driver
from src.db.postgres import get_postgres_driver
from src.db.redis import get_redis_driver
from src.memory.enrichment_queue import (
    start_memory_enrichment_worker,
    stop_memory_enrichment_worker,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    logger = get_logger(__name__)

    # Startup
    logger.info("application_starting")

    # Initialize database connections (graceful degradation)
    neo4j_driver = get_neo4j_driver()
    postgres_driver = get_postgres_driver()
    redis_driver = get_redis_driver()

    connected = {"neo4j": False, "postgres": False, "redis": False}

    try:
        await neo4j_driver.connect()
        connected["neo4j"] = True
        logger.info("neo4j_startup_connected")
    except Exception as e:
        logger.warning("neo4j_startup_failed", error=str(e))

    try:
        await postgres_driver.connect()
        connected["postgres"] = True
        logger.info("postgres_startup_connected")
    except Exception as e:
        logger.warning("postgres_startup_failed", error=str(e))

    try:
        await redis_driver.connect()
        connected["redis"] = True
        logger.info("redis_startup_connected")
    except Exception as e:
        logger.warning("redis_startup_failed", error=str(e))

    # Store on app.state for access in routes
    app.state.neo4j = neo4j_driver
    app.state.postgres = postgres_driver
    app.state.redis = redis_driver
    app.state.db_connected = connected

    if connected["neo4j"] and connected["postgres"]:
        try:
            await start_memory_enrichment_worker()
        except Exception as e:
            logger.warning("enrichment_worker_start_failed", error=str(e))

    logger.info("application_started", **connected)

    yield

    # Shutdown
    logger.info("application_shutting_down")

    try:
        await stop_memory_enrichment_worker()
    except Exception:
        pass

    if connected["neo4j"]:
        try:
            await neo4j_driver.disconnect()
        except Exception:
            pass
    if connected["postgres"]:
        try:
            await postgres_driver.disconnect()
        except Exception:
            pass
    if connected["redis"]:
        try:
            await redis_driver.disconnect()
        except Exception:
            pass

    logger.info("databases_disconnected")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging()
    settings = get_settings()
    
    app = FastAPI(
        title="NeuroGraph API",
        description="An agentic context engine with explainable graph memory",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )
    
    # Add middleware
    app.middleware("http")(logging_middleware)
    app.middleware("http")(error_handler_middleware)
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Include MCP HTTP transport
    app.include_router(mcp_router, prefix="/api/v1")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}
    
    @app.get("/ready")
    async def readiness_check() -> dict[str, bool]:
        """Readiness check with database connectivity."""
        connected = getattr(app.state, "db_connected", {})
        neo4j_healthy = await get_neo4j_driver().health_check() if connected.get("neo4j") else False
        postgres_healthy = await get_postgres_driver().health_check() if connected.get("postgres") else False
        redis_healthy = await get_redis_driver().health_check() if connected.get("redis") else False
        ready = neo4j_healthy and postgres_healthy

        return {
            "ready": ready,
            "neo4j": neo4j_healthy,
            "postgres": postgres_healthy,
            "redis": redis_healthy,
        }
    
    return app


# Create the application instance
app = create_app()
