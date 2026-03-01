"""Circuit breaker pattern for handling repeated failures."""

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

from isaforge.core.exceptions import CircuitBreakerOpenError
from isaforge.observability.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """State of the circuit breaker."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """Circuit breaker to prevent cascading failures.

    When a service fails repeatedly, the circuit breaker "opens" and
    rejects further calls for a timeout period. After the timeout,
    it enters "half-open" state and allows a test call through.
    If the test succeeds, the circuit closes; if it fails, it opens again.
    """

    name: str
    max_failures: int = 3
    timeout_seconds: float = 60.0
    half_open_max_calls: int = 1

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float | None = field(default=None, init=False)
    _half_open_calls: int = field(default=0, init=False)

    @property
    def state(self) -> CircuitState:
        """Get the current state, checking for timeout transition."""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time is not None:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.timeout_seconds:
                    logger.info(
                        "circuit_breaker_half_open",
                        name=self.name,
                        elapsed_seconds=elapsed,
                    )
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
        return self._state

    def _record_success(self) -> None:
        """Record a successful call."""
        if self._state == CircuitState.HALF_OPEN:
            logger.info("circuit_breaker_closed", name=self.name)
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0

    def _record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            logger.warning(
                "circuit_breaker_reopened",
                name=self.name,
                failure_count=self._failure_count,
            )
            self._state = CircuitState.OPEN
        elif self._failure_count >= self.max_failures:
            logger.warning(
                "circuit_breaker_opened",
                name=self.name,
                failure_count=self._failure_count,
                timeout_seconds=self.timeout_seconds,
            )
            self._state = CircuitState.OPEN

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute a function through the circuit breaker.

        Args:
            func: Function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            The function's return value.

        Raises:
            CircuitBreakerOpenError: If the circuit is open.
            Exception: Any exception from the function.
        """
        current_state = self.state  # This checks for timeout transition

        if current_state == CircuitState.OPEN:
            logger.debug(
                "circuit_breaker_rejected",
                name=self.name,
                state=current_state.value,
            )
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is open. "
                f"Try again in {self.timeout_seconds - (time.time() - (self._last_failure_time or 0)):.1f}s"
            )

        if current_state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1
            if self._half_open_calls > self.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is half-open and at max test calls"
                )

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise e

    async def call_async(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute an async function through the circuit breaker.

        Args:
            func: Async function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            The function's return value.

        Raises:
            CircuitBreakerOpenError: If the circuit is open.
            Exception: Any exception from the function.
        """
        current_state = self.state

        if current_state == CircuitState.OPEN:
            logger.debug(
                "circuit_breaker_rejected",
                name=self.name,
                state=current_state.value,
            )
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is open. "
                f"Try again in {self.timeout_seconds - (time.time() - (self._last_failure_time or 0)):.1f}s"
            )

        if current_state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1
            if self._half_open_calls > self.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is half-open and at max test calls"
                )

        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise e

    def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        logger.info("circuit_breaker_reset", name=self.name)
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    _breakers: dict[str, CircuitBreaker] = {}

    @classmethod
    def get_or_create(
        cls,
        name: str,
        max_failures: int = 3,
        timeout_seconds: float = 60.0,
    ) -> CircuitBreaker:
        """Get an existing circuit breaker or create a new one.

        Args:
            name: Name of the circuit breaker.
            max_failures: Number of failures before opening.
            timeout_seconds: Seconds to wait before half-opening.

        Returns:
            The circuit breaker instance.
        """
        if name not in cls._breakers:
            cls._breakers[name] = CircuitBreaker(
                name=name,
                max_failures=max_failures,
                timeout_seconds=timeout_seconds,
            )
        return cls._breakers[name]

    @classmethod
    def get(cls, name: str) -> CircuitBreaker | None:
        """Get a circuit breaker by name.

        Args:
            name: Name of the circuit breaker.

        Returns:
            The circuit breaker or None if not found.
        """
        return cls._breakers.get(name)

    @classmethod
    def reset_all(cls) -> None:
        """Reset all circuit breakers."""
        for breaker in cls._breakers.values():
            breaker.reset()
