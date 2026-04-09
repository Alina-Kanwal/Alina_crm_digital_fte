"""
Main FastAPI application for Digital FTE Agent.

Production-grade setup with:
- Structured logging with correlation IDs
- Request metrics and tracing
- Health checks (liveness and readiness)
- Graceful startup/shutdown
- Error handling middleware
"""
import os
import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, Info, make_asgi_app

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry dependencies, fallback to mock if not available
try:
    from opentelemetry import trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    logger.warning("OpenTelemetry not available, using mock tracing")
    OPENTELEMETRY_AVAILABLE = False

    # Mock OpenTelemetry dependencies
    class MockTracerProvider:
        def __init__(self, **kwargs):
            pass
        def add_span_processor(self, processor):
            pass

    class MockConsoleSpanExporter:
        def __init__(self):
            pass

    class MockResource:
        @staticmethod
        def create(attributes):
            return MockResource()

    trace = type('trace', (), {
        'set_tracer_provider': lambda x: None,
        'get_tracer_provider': lambda: None
    })()

    FastAPIInstrumentor = type('FastAPIInstrumentor', (), {
        'instrument_app': lambda x: None
    })()

    TracerProvider = MockTracerProvider
    ConsoleSpanExporter = MockConsoleSpanExporter
    Resource = MockResource

# Configure structured logging
from src.middleware.logging import configure_logging

# Configure database
from src.database.connection import init_db, close_db, check_db_health


# Initialize structured logging
configure_logging()

# Create FastAPI app with production settings
app = FastAPI(
    title="Digital FTE Agent API",
    description="Production-grade AI Customer Success Agent API with multi-channel support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)
INFO = Info("digital_fte_api", "Digital FTE API")
INFO.info({"version": "1.0.0"})

# OpenTelemetry tracing setup (conditional)
if OPENTELEMETRY_AVAILABLE:
    resource = Resource.create({
        "service.name": "digital-fte-api",
        "service.version": "1.0.0",
    })
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(ConsoleSpanExporter())
    trace.set_tracer_provider(tracer_provider)

    # Instrument FastAPI for tracing
    FastAPIInstrumentor.instrument_app(app)

# Add CORS middleware (production settings would be tighter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add Prometheus metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to track request metrics."""
    method = request.method
    path = request.url.path

    try:
        with REQUEST_DURATION.labels(method=method, endpoint=path).time():
            response = await call_next(request)
            REQUEST_COUNT.labels(
                method=method, endpoint=path, status=response.status_code
            ).inc()
            return response
    except Exception as e:
        REQUEST_COUNT.labels(
            method=method, endpoint=path, status=500
        ).inc()
        raise

# Add correlation ID middleware
from src.middleware.correlation import CorrelationIDMiddleware
app.add_middleware(CorrelationIDMiddleware)

# Add structured logging middleware
from src.middleware.logging import LoggingMiddleware
app.add_middleware(LoggingMiddleware)

# Add error handling middleware
from src.middleware.errors import ErrorHandlerMiddleware
app.add_middleware(ErrorHandlerMiddleware)

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    logger.info("Starting Digital FTE Agent API...")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


    # 🚀 Start Digital FTE Living Agent (24/7 Autonomous Brain)
    from src.services.living_agent import living_agent
    asyncio.create_task(living_agent.start_working_247())

    logger.info("Digital FTE Agent API startup complete")

    yield

    # Shutdown: cleanup resources
    logger.info("Shutting down Digital FTE Agent API...")
    await close_db()


    logger.info("Digital FTE Agent API shutdown complete")

app.router.lifespan_context = lifespan

# Health check endpoints (Kubernetes compatibility)
@app.get("/health/live", tags=["health"])
async def liveness_probe():
    """
    Liveness probe - checks if application is running.

    Returns 200 if application is alive, 503 otherwise.
    """
    return {"status": "alive", "service": "digital-fte-api"}

@app.get("/health/ready", tags=["health"])
async def readiness_probe():
    """
    Readiness probe - checks if application is ready to serve requests.

    Returns 200 if ready, 503 otherwise.

    Checks:
    - Database connection
    """
    checks = {
        "database": "ready" if check_db_health() else "not_ready",
    }


    # Overall status
    all_ready = all(status == "ready" for status in checks.values())

    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
    }

@app.get("/health/startup", tags=["health"])
async def startup_probe():
    """
    Startup probe - checks if application has completed startup.

    Always returns 200 if we've reached this point.
    """
    return {"status": "started", "service": "digital-fte-api"}

# Metrics endpoint (Prometheus)
@app.get("/metrics", tags=["metrics"])
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Digital FTE Agent API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": {
            "liveness": "/health/live",
            "readiness": "/health/ready",
            "startup": "/health/startup",
        },
        "metrics": "/metrics",
    }

# API v1 routers
from src.api import inquiries, tickets, reports, escalation, crm
app.include_router(inquiries.router, prefix="/api/v1/inquiries", tags=["inquiries"])
app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["tickets"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(escalation.router, prefix="/api/v1/escalation", tags=["escalation"])
app.include_router(crm.router, prefix="/api/v1/crm", tags=["crm"])

# Expose Prometheus ASGI app for metrics scraping
metrics_app = make_asgi_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENVIRONMENT", "production").lower() == "development",
        workers=int(os.getenv("WORKERS", "1")),
        access_log=True,
    )
