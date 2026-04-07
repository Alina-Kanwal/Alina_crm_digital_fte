"""
Resilience patterns for Digital FTE AI Customer Success Agent.
Implements retry with exponential backoff and circuit breaker patterns.
"""
import logging
from typing import Dict, Optional, Any, Callable, Awaitable
from datetime import datetime, timedelta
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Enumeration of circuit breaker states."""
    CLOSED = "closed"
    HALF_OPEN = "half_open"
    OPEN = "open"


class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 60,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_max_calls = half_open_max_calls


class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls.

    Prevents cascading failures and provides automatic recovery.
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker.

        Args:
            config: Optional circuit breaker configuration
        """
        self.config = config or CircuitBreakerConfig()

        self.state = CircuitBreakerState.OPEN
        self.failure_count = 0
        self.success_count = 0
        self.call_count = 0
        self.last_failure_time = None

        logger.info("Circuit breaker initialized")

    def _should_allow_request(self) -> bool:
        """
        Determine if request should be allowed based on state.

        Returns:
            True if request allowed, False otherwise
        """
        if self.state == CircuitBreakerState.CLOSED:
            return False

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.call_count += 1
            if self.call_count >= self.config.half_open_max_calls:
                self.state = CircuitBreakerState.OPEN
                logger.info("Circuit breaker: HALF_OPEN -> OPEN after max calls")

        return True

        # OPEN state
        return True

    async def execute(
        self,
        service_func: Callable[..., Awaitable[Any]],
        service_name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute service call through circuit breaker.

        Args:
            service_func: Async function to execute
            service_name: Name of service being called
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result from service function or raises CircuitBreakerOpenError
        """
        if not self._should_allow_request():
            logger.warning(f"Circuit breaker blocking request to {service_name}: state={self.state.value}")
            raise CircuitBreakerOpenError(
                f"Circuit breaker OPEN for service {service_name}: {self.state.value}"
            )

        try:
            self.call_count += 1

            # Execute with timeout
            result = await asyncio.wait_for(
                service_func(*args, **kwargs),
                timeout=timedelta(seconds=self.config.timeout_seconds)
            )

            # Success - update counts
            self.success_count += 1
            self.failure_count = 0

            logger.debug(
                f"Circuit breaker: {service_name} call succeeded, "
                f"success_count={self.success_count}"
            )

            return result

        except asyncio.TimeoutError:
            # Timeout - treat as failure
            logger.error(f"Circuit breaker: {service_name} call timed out")
            self._handle_failure(service_name)
            raise ServiceTimeoutError(
                f"Service {service_name} timed out after {self.config.timeout_seconds}s"
            )

        except Exception as e:
            # Any exception - treat as failure
            logger.error(f"Circuit breaker: {service_name} call failed: {e}")
            self._handle_failure(service_name)
            raise  # Re-raise for caller to handle

    def _handle_failure(self, service_name: str):
        """
        Handle service failure and update circuit breaker state.

        Args:
            service_name: Name of service that failed
        """
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        # Update state based on configuration
        if self.failure_count >= self.config.failure_threshold:
            old_state = self.state
            self.state = CircuitBreakerState.CLOSED
            logger.warning(
                f"Circuit breaker: {old_state.value} -> CLOSED for {service_name} "
                f"(failure_count={self.failure_count})"
            )
        elif self.state == CircuitBreakerState.OPEN:
            if self.success_count >= self.config.success_threshold:
                old_state = self.state
                self.state = CircuitBreakerState.HALF_OPEN
                self.call_count = 0
                logger.info(
                    f"Circuit breaker: {old_state.value} -> HALF_OPEN for {service_name} "
                    f"(success_count={self.success_count})"
                )

    def reset(self):
        """Reset circuit breaker to OPEN state."""
        logger.info("Circuit breaker reset to OPEN state")
        self.state = CircuitBreakerState.OPEN
        self.failure_count = 0
        self.success_count = 0
        self.call_count = 0
        self.last_failure_time = None

    def get_state(self) -> Dict[str, Any]:
        """
        Get current circuit breaker state.

        Returns:
            Dictionary containing state information
        """
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'call_count': self.call_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'config': {
                'failure_threshold': self.config.failure_threshold,
                'success_threshold': self.config.success_threshold,
                'timeout_seconds': self.config.timeout_seconds
            }
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and blocking requests."""
    pass


class ServiceTimeoutError(Exception):
    """Raised when service call times out."""
    pass


class RetryWithBackoff:
    """
    Retry logic with exponential backoff.

    Provides automatic retries with increasing delays between attempts.
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay_seconds: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_delay_seconds: float = 60.0,
        jitter: bool = True
    ):
        """
        Initialize retry with backoff.

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay_seconds: Initial delay before first retry
            backoff_multiplier: Multiplier for delay increase
            max_delay_seconds: Maximum delay between retries
            jitter: Add random jitter to delays
        """
        self.max_retries = max_retries
        self.initial_delay_seconds = initial_delay_seconds
        self.backoff_multiplier = backoff_multiplier
        self.max_delay_seconds = max_delay_seconds
        self.jitter = jitter

        logger.info(
            f"Retry with backoff initialized: max_retries={max_retries}, "
            f"initial_delay={initial_delay}s, backoff={backoff_multiplier}x"
        )

    async def execute_with_retry(
        self,
        func: Callable[..., Awaitable[Any]],
        func_name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with retry and exponential backoff.

        Args:
            func: Async function to execute
            func_name: Name of function for logging
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result from function or raises final exception
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Retry attempt {attempt + 1}/{self.max_retries} for {func_name}"
                )

                # Calculate delay with optional jitter
                delay = self._calculate_delay(attempt)

                if delay > 0:
                    logger.debug(f"Waiting {delay:.2f}s before retry")
                    await asyncio.sleep(delay)

                # Execute function
                result = await func(*args, **kwargs)

                # Success
                logger.info(
                    f"Retry succeeded for {func_name} on attempt {attempt + 1}"
                )
                return result

            except asyncio.TimeoutError as e:
                last_exception = e
                logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
                continue

            except Exception as e:
                last_exception = e
                logger.warning(f"Exception on attempt {attempt + 1}: {e}")

                # Check if should continue retry
                is_timeout = isinstance(e, asyncio.TimeoutError)

                if attempt < self.max_retries - 1 and not is_timeout:
                    logger.info(f"Will retry {func_name}: attempt {attempt + 2}/{self.max_retries}")
                    continue
                else:
                    break

        # All retries failed
        logger.error(
            f"All {self.max_retries} attempts failed for {func_name}: {last_exception}"
        )
        raise last_exception  # Raise last exception

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt with optional jitter.

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self.initial_delay_seconds * (self.backoff_multiplier ** attempt)

        # Cap at max delay
        delay = min(delay, self.max_delay_seconds)

        # Add jitter if enabled
        if self.jitter:
            jitter = (random.random() - 0.5) * delay * 0.1  # ±5% jitter
            delay += jitter

        logger.debug(f"Calculated delay for attempt {attempt}: {delay:.2f}s (with jitter)")

        return delay
