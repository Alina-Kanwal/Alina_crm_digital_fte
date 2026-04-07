"""
Distributed tracing using OpenTelemetry.

Provides tracing setup, span management, and integration
with FastAPI for end-to-end request tracing.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)
from typing import Optional, Dict, Any, Callable
from contextvars import ContextVar

# Try to import OpenTelemetry dependencies, fallback to mock if not available
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.semconv.trace import SemanticConventions
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    from opentelemetry.trace.propagation.b3 import B3MultiFormatPropagator
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

    # Mock SemanticConventions
    class MockSemanticConventions:
        HTTP_METHOD = "http.method"
        HTTP_URL = "http.url"
        HTTP_HOST = "http.host"
        HTTP_SCHEME = "http.scheme"
        HTTP_FLAVOR = "http.flavor"
        HTTP_STATUS_CODE = "http.status_code"

    class MockStatus:
        OK = type('OK', (), {})()
        ERROR = type('ERROR', (), {})()

    class MockStatusCode:
        OK = type('OK', (), {})()
        ERROR = type('ERROR', (), {})()

    # Mock propagators
    class MockTraceContextTextMapPropagator:
        def inject(self, ctx, headers):
            pass

    class MockB3MultiFormatPropagator:
        def inject(self, ctx, headers):
            pass

    trace = type('trace', (), {
        'get_tracer_provider': lambda: None,
        'set_tracer_provider': lambda x: None,
        'get_current_span': lambda: None,
        'get_current': lambda: None,
    })()

    TracerProvider = MockTracerProvider
    ConsoleSpanExporter = MockConsoleSpanExporter
    Resource = MockResource
    SemanticConventions = MockSemanticConventions()
    Status = MockStatus
    StatusCode = MockStatusCode
    TraceContextTextMapPropagator = MockTraceContextTextMapPropagator()
    B3MultiFormatPropagator = MockB3MultiFormatPropagator()

from fastapi import Request

logger = logging.getLogger(__name__)

# Trace context variable
_trace_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar("trace_context", default=None)


class OpenTelemetryConfig:
    """
    OpenTelemetry configuration.

    Defines service name, resource attributes, and exporters.
    """

    SERVICE_NAME = "digital-fte-api"
    SERVICE_VERSION = "1.0.0"
    ENVIRONMENT = "production"  # Will be dynamic

    # Resource attributes
    RESOURCE_ATTRIBUTES = {
        "service.name": SERVICE_NAME,
        "service.version": SERVICE_VERSION,
        "deployment.environment": ENVIRONMENT,
    }

    # Span names
    SPAN_NAMES = {
        "http_request": "http.request",
        "db_query": "db.query",
        "kafka_produce": "kafka.produce",
        "kafka_consume": "kafka.consume",
        "agent_request": "agent.request",
        "cache_get": "cache.get",
        "cache_set": "cache.set",
    }


def setup_opentelemetry(
    service_name: str = OpenTelemetryConfig.SERVICE_NAME,
    service_version: str = OpenTelemetryConfig.SERVICE_VERSION,
    environment: str = "development",
) -> TracerProvider:
    """
    Set up OpenTelemetry tracing.

    Args:
        service_name: Service name
        service_version: Service version
        environment: Deployment environment

    Returns:
        TracerProvider instance
    """
    # Create resource
    resource = Resource.create({
        **OpenTelemetryConfig.RESOURCE_ATTRIBUTES,
        "service.name": service_name,
        "service.version": service_version,
        "deployment.environment": environment,
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add span processor
    def add_service_info(span, context):
        """Add service information to span."""
        span.set_attribute("service.name", service_name)
        span.set_attribute("service.version", service_version)
        span.set_attribute("deployment.environment", environment)

    provider.add_span_processor(add_service_info)

    # Add console exporter (replace with OTLP in production)
    provider.add_span_processor(ConsoleSpanExporter())

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    logger.info(f"OpenTelemetry configured: {service_name} v{service_version} ({environment})")
    return provider


def get_current_span():
    """
    Get current span from context.

    Returns:
        Current span or None
    """
    return trace.get_current_span()


def set_trace_context(attributes: Dict[str, Any]) -> None:
    """
    Set trace context in context variable.

    Args:
        attributes: Trace attributes to store
    """
    current_context = _trace_context.get() or {}
    current_context.update(attributes)
    _trace_context.set(current_context)


def get_trace_context() -> Optional[Dict[str, Any]]:
    """
    Get trace context from context variable.

    Returns:
        Trace context dictionary or None
    """
    return _trace_context.get()


class Tracer:
    """
    Wrapper around OpenTelemetry tracer.

    Provides convenient methods for creating spans
    with automatic attribute setting.
    """

    def __init__(
        self,
        tracer_name: str = OpenTelemetryConfig.SERVICE_NAME,
    ):
        """
        Initialize tracer.

        Args:
            tracer_name: Tracer name
        """
        self.tracer = trace.get_tracer(tracer_name)

    def create_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        parent: Optional[Any] = None,
    ):
        """
        Create a new span.

        Args:
            name: Span name
            attributes: Optional span attributes
            parent: Optional parent span

        Returns:
            Span context manager
        """
        return self.tracer.start_as_current_span(
            name=name,
            attributes=attributes,
        )

    def record_exception(
        self,
        exception: Exception,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """
        Record exception in current span.

        Args:
            exception: Exception to record
            attributes: Optional additional attributes
        """
        current_span = get_current_span()
        if current_span:
            current_span.record_exception(exception)

            if attributes:
                for key, value in attributes.items():
                    current_span.set_attribute(key, value)

    def set_status(
        self,
        status: Status,
        description: Optional[str] = None,
    ):
        """
        Set span status.

        Args:
            status: Span status
            description: Optional status description
        """
        current_span = get_current_span()
        if current_span:
            current_span.set_status(status)
            if description:
                current_span.set_attribute("status.description", description)

    def add_event(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """
        Add event to current span.

        Args:
            name: Event name
            attributes: Optional event attributes
        """
        current_span = get_current_span()
        if current_span:
            current_span.add_event(name, attributes=attributes or {})

    def add_attributes(self, attributes: Dict[str, Any]) -> None:
        """
        Add attributes to current span.

        Args:
            attributes: Attributes to add
        """
        current_span = get_current_span()
        if current_span:
            for key, value in attributes.items():
                current_span.set_attribute(key, value)


# Singleton tracer instance
_tracer: Optional[Tracer] = None


def get_tracer() -> Tracer:
    """
    Get or create singleton tracer.

    Returns:
        Tracer instance
    """
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


class TracingMiddleware:
    """
    FastAPI middleware for request tracing.

    Creates spans for all HTTP requests and adds
    context propagation using W3C and B3 formats.
    """

    def __init__(self, app):
        """
        Initialize tracing middleware.

        Args:
            app: FastAPI application
        """
        self.app = app
        self.tracer = get_tracer()

    async def __call__(self, scope, receive, send):
        # Handle ASGI interface
        if isinstance(scope, dict) and callable(receive) and callable(send):
            # Import here to avoid circular imports
            from starlette.requests import Request

            request = Request(scope, receive)

            # Extract trace context from incoming request
            traceparent = request.headers.get("traceparent")
            tracestate = request.headers.get("tracestate")

            with self.tracer.create_span(
                name=OpenTelemetryConfig.SPAN_NAMES["http_request"],
            ) as span:
                # Add HTTP attributes
                span.set_attribute(SemanticConventions.HTTP_METHOD, request.method)
                span.set_attribute(SemanticConventions.HTTP_URL, str(request.url))
                span.set_attribute(SemanticConventions.HTTP_HOST, request.client.host if request.client else "unknown")
                span.set_attribute(SemanticConventions.HTTP_SCHEME, request.url.scheme)
                span.set_attribute(SemanticConventions.HTTP_FLAVOR, request.scope["type"])

                # Add correlation ID
                correlation_id = self._get_correlation_id_from_scope(scope)
                if correlation_id:
                    span.set_attribute("correlation.id", correlation_id)

                # Add user agent if available
                user_agent = request.headers.get("user-agent")
                if user_agent:
                    span.set_attribute("http.user_agent", user_agent)

                # Process request
                try:
                    # Call the next middleware/app in the chain
                    await self.app(scope, receive, send)
                    return
                except Exception as e:
                    # Record exception
                    span.record_exception(e)
                    span.set_status(Status.ERROR, description=str(e))
                    # Re-raise to let error handling middleware deal with it
                    raise
        else:
            # Legacy fallback - this should not happen in normal operation
            raise ValueError("Invalid ASGI interface")

    def _get_correlation_id_from_scope(self, scope):
        """Extract correlation ID from ASGI scope."""
        try:
            # Look for correlation ID in scope state or headers
            headers = dict(scope.get("headers", []))
            # Convert byte keys/values to strings
            headers = {k.decode("latin-1") if isinstance(k, bytes) else k:
                      v.decode("latin-1") if isinstance(v, bytes) else v
                      for k, v in headers.items()}

            # Look for correlation ID in headers
            correlation_id = headers.get("x-correlation-id")
            if correlation_id:
                return correlation_id

            # Alternative header names
            correlation_id = headers.get("correlationid")
            if correlation_id:
                return correlation_id

            return "unknown"
        except Exception:
            return "unknown"
        """
        Process request with tracing.

        Args:
            request: Incoming request
            call_next: Next middleware or route handler

        Returns:
            Response from downstream
        """
        # Extract trace context from incoming request
        traceparent = request.headers.get("traceparent")
        tracestate = request.headers.get("tracestate")

        with self.tracer.create_span(
            name=OpenTelemetryConfig.SPAN_NAMES["http_request"],
        ) as span:
            # Add HTTP attributes
            span.set_attribute(SemanticConventions.HTTP_METHOD, request.method)
            span.set_attribute(SemanticConventions.HTTP_URL, str(request.url))
            span.set_attribute(SemanticConventions.HTTP_HOST, request.client.host if request.client else "unknown")
            span.set_attribute(SemanticConventions.HTTP_SCHEME, request.url.scheme)
            span.set_attribute(SemanticConventions.HTTP_FLAVOR, request.scope["type"])

            # Add correlation ID
            correlation_id = getattr(request.state, "correlation_id", None)
            if correlation_id:
                span.set_attribute("correlation.id", correlation_id)

            # Add user agent if available
            user_agent = request.headers.get("user-agent")
            if user_agent:
                span.set_attribute("http.user_agent", user_agent)

            # Process request
            try:
                response = await call_next(request)

                # Add response attributes
                span.set_attribute(SemanticConventions.HTTP_STATUS_CODE, response.status_code)

                # Set span status based on status code
                if 200 <= response.status_code < 300:
                    span.set_status(Status.OK)
                elif 400 <= response.status_code < 500:
                    span.set_status(Status.ERROR)
                    span.set_attribute("error.type", "http_4xx_error")
                elif 500 <= response.status_code < 600:
                    span.set_status(Status.ERROR)
                    span.set_attribute("error.type", "http_5xx_error")

                return response

            except Exception as e:
                # Record exception
                span.record_exception(e)
                span.set_status(Status.ERROR, description=str(e))
                raise


# Propagators for trace context propagation
propagators = [
    TraceContextTextMapPropagator,
    B3MultiFormatPropagator,
]


def inject_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Inject trace context into headers for outbound requests.

    Args:
        headers: Existing headers dictionary

    Returns:
        Updated headers with trace context
    """
    tracer = get_tracer().tracer
    ctx = trace.get_current()

    if ctx:
        for propagator_class in propagators:
            propagator = propagator_class()
            propagator.inject(ctx, headers)

    return headers


def extract_trace_context(headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Extract trace context from headers.

    Args:
        headers: Incoming headers

    Returns:
        Trace context or None
    """
    ctx = trace.get_current()

    if ctx:
        return {
            "trace_id": ctx.span_id,
            "span_id": ctx.span_id,
            "trace_flags": ctx.trace_flags,
        }

    return None
