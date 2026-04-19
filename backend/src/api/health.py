"""
Health check endpoints for Kubernetes probes.

Provides liveness and readiness probes for Kubernetes deployment.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from src.database.connection import check_db_health, get_db_pool_stats

# Kafka producer import with fallback
try:
    from src.kafka.producer import get_producer
except ImportError:
    # Fallback if kafka.producer module has issues
    def get_producer():
        return None

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/live")
async def liveness() -> JSONResponse:
    """
    Liveness probe - checks if application is running.

    Kubernetes uses this to know if the container needs to be restarted.

    Returns:
        JSONResponse with liveness status
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "digital-fte-api",
        },
    )


@router.get("/ready")
async def readiness() -> JSONResponse:
    """
    Readiness probe - checks if application is ready to serve requests.

    Kubernetes uses this to know if the pod can receive traffic.

    Checks:
    - Database connection
    - Kafka producer (optional - doesn't fail readiness if unavailable)

    Returns:
        JSONResponse with readiness status
    """
    checks: Dict[str, Any] = {}

    # Check database
    db_healthy = check_db_health()
    db_info = {}
    if db_healthy:
        db_info["pool_stats"] = get_db_pool_stats()
    else:
        db_info["error"] = "Database connection failed"

    checks["database"] = {
        "status": "healthy" if db_healthy else "unhealthy",
        **db_info,
    }

    # Check Kafka producer (optional - doesn't fail readiness)
    kafka_healthy = False
    kafka_message = "not_configured"

    try:
        producer = get_producer()
        if producer:
            kafka_healthy = True
            kafka_message = "connected"
        else:
            kafka_healthy = False
            kafka_message = "not_initialized"
    except Exception as e:
        kafka_healthy = False
        kafka_message = f"error: {str(e)}"

    checks["kafka"] = {
        "status": "healthy" if kafka_healthy else "degraded",
        "message": kafka_message,
    }

    # Overall readiness (only database is critical)
    overall_healthy = db_healthy

    status_code = 200 if overall_healthy else 503
    status = "ready" if overall_healthy else "not_ready"

    return JSONResponse(
        status_code=status_code,
        content={
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
        },
    )


@router.get("/startup")
async def startup() -> JSONResponse:
    """
    Startup probe - checks if application has completed startup.

    Kubernetes can use this to know if the application has finished initializing.

    Always returns 200 if this endpoint is reachable.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "started",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "digital-fte-api",
        },
    )


@router.get("/")
async def root() -> JSONResponse:
    """
    Root endpoint with API information.

    Returns:
        JSONResponse with API details and navigation links.
    """
    return JSONResponse(
        status_code=200,
        content={
            "service": "Digital FTE Agent API",
            "version": "1.0.0",
            "status": "operational",
            "endpoints": {
                "health": {
                    "liveness": "/health/live",
                    "readiness": "/health/ready",
                    "startup": "/health/startup",
                },
                "api": {
                    "inquiries": "/api/v1/inquiries",
                    "tickets": "/api/v1/tickets",
                    "reports": "/api/v1/reports",
                },
                "docs": {
                    "swagger": "/docs",
                    "redoc": "/redoc",
                },
            },
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@router.get("/health")
async def health() -> JSONResponse:
    """
    Comprehensive health check endpoint.

    Returns detailed health information including:
    - Service status
    - Database health
    - Kafka health
    - Version information

    Returns:
        JSONResponse with comprehensive health status
    """
    checks: Dict[str, Any] = {
        "database": {"status": "unknown"},
        "kafka": {"status": "unknown"},
    }

    # Check database
    try:
        db_healthy = check_db_health()
        db_info = {}
        if db_healthy:
            db_info["pool_stats"] = get_db_pool_stats()
        else:
            db_info["error"] = "Database connection failed"

        checks["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            **db_info,
        }
    except Exception as e:
        checks["database"] = {
            "status": "error",
            "error": str(e),
        }

    # Check Kafka
    try:
        producer = get_producer()
        if producer:
            checks["kafka"] = {"status": "healthy"}
        else:
            checks["kafka"] = {"status": "not_configured"}
    except Exception as e:
        checks["kafka"] = {
            "status": "error",
            "error": str(e),
        }

    # Determine overall health
    all_healthy = all(
        check.get("status") in ["healthy", "not_configured"]
        for check in checks.values()
    )

    overall_status = "healthy" if all_healthy else "degraded"
    status_code = 200 if overall_status == "healthy" else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "digital-fte-api",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "checks": checks,
        },
    )


@router.get("/metrics")
async def metrics() -> PlainTextResponse:
    """
    Prometheus metrics endpoint.

    Returns Prometheus metrics for scraping.

    Returns:
        PlainTextResponse with Prometheus metrics format
    """
    # This endpoint is handled by the Prometheus ASGI app in main.py
    # We'll return a simple message here
    return PlainTextResponse(
        "Metrics are available at /metrics (handled by Prometheus ASGI app)",
        status_code=200,
    )
