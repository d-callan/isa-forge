"""Unit tests for observability modules."""

import time

from isaforge.observability.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitState,
)
from isaforge.observability.metrics import (
    MetricsCollector,
    OperationMetrics,
    SessionMetrics,
    Timer,
)
from isaforge.observability.logger import get_logger


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_initial_state_closed(self):
        """Test circuit breaker starts in closed state."""
        cb = CircuitBreaker(name="test")
        assert cb.state == CircuitState.CLOSED

    def test_call_success_keeps_closed(self):
        """Test successful calls keep circuit closed."""
        cb = CircuitBreaker(name="test", max_failures=3)

        def success_func():
            return "ok"

        result = cb.call(success_func)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    def test_failures_open_circuit(self):
        """Test failures at threshold open the circuit."""
        cb = CircuitBreaker(name="test_open", max_failures=2)

        def fail_func():
            raise ValueError("fail")

        # Record failures
        for _ in range(2):
            try:
                cb.call(fail_func)
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN

    def test_reset(self):
        """Test resetting the circuit breaker."""
        cb = CircuitBreaker(name="test_reset", max_failures=2)

        def fail_func():
            raise ValueError("fail")

        for _ in range(2):
            try:
                cb.call(fail_func)
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN

        cb.reset()
        assert cb.state == CircuitState.CLOSED

    def test_half_open_after_timeout(self):
        """Test circuit transitions to half-open after timeout."""
        cb = CircuitBreaker(name="test_halfopen", max_failures=2, timeout_seconds=0.01)

        def fail_func():
            raise ValueError("fail")

        for _ in range(2):
            try:
                cb.call(fail_func)
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.02)

        # Should transition to half-open on state check
        assert cb.state == CircuitState.HALF_OPEN


class TestCircuitBreakerRegistry:
    """Test circuit breaker registry."""

    def test_get_or_create(self):
        """Test getting or creating circuit breakers."""
        cb1 = CircuitBreakerRegistry.get_or_create("registry_test")
        cb2 = CircuitBreakerRegistry.get_or_create("registry_test")
        assert cb1 is cb2

    def test_get_nonexistent(self):
        """Test getting nonexistent circuit breaker."""
        result = CircuitBreakerRegistry.get("nonexistent_cb")
        assert result is None

    def test_reset_all(self):
        """Test resetting all circuit breakers."""
        cb = CircuitBreakerRegistry.get_or_create("reset_all_test", max_failures=1)

        def fail_func():
            raise ValueError("fail")

        try:
            cb.call(fail_func)
        except ValueError:
            pass

        assert cb.state == CircuitState.OPEN

        CircuitBreakerRegistry.reset_all()
        assert cb.state == CircuitState.CLOSED


class TestOperationMetrics:
    """Test operation metrics."""

    def test_creation(self):
        """Test creating operation metrics."""
        metrics = OperationMetrics(name="test_op")
        assert metrics.name == "test_op"
        assert metrics.success is True

    def test_duration(self):
        """Test duration calculation."""
        metrics = OperationMetrics(name="test_op")
        time.sleep(0.01)
        assert metrics.duration_ms > 0

    def test_complete(self):
        """Test completing operation."""
        metrics = OperationMetrics(name="test_op")
        metrics.complete(success=False, error="test error")
        assert metrics.success is False
        assert metrics.error == "test error"
        assert metrics.end_time is not None


class TestSessionMetrics:
    """Test session metrics."""

    def test_creation(self):
        """Test creating session metrics."""
        metrics = SessionMetrics(session_id="test-session")
        assert metrics.session_id == "test-session"
        assert metrics.total_llm_calls == 0

    def test_record_llm_call(self):
        """Test recording LLM call."""
        metrics = SessionMetrics(session_id="test-session")
        metrics.record_llm_call(prompt_tokens=100, completion_tokens=50, latency_ms=500)

        assert metrics.total_llm_calls == 1
        assert metrics.total_prompt_tokens == 100
        assert metrics.total_completion_tokens == 50

    def test_record_tool_call(self):
        """Test recording tool call."""
        metrics = SessionMetrics(session_id="test-session")
        metrics.record_tool_call(tool_name="fetch_bioproject", success=True, latency_ms=200)

        assert metrics.total_tool_calls == 1
        assert metrics.tool_call_counts["fetch_bioproject"] == 1

    def test_record_field_decision(self):
        """Test recording field decision."""
        metrics = SessionMetrics(session_id="test-session")
        metrics.record_field_decision("auto_accepted")
        metrics.record_field_decision("user_edited")

        assert metrics.total_fields == 2
        assert metrics.auto_accepted_fields == 1
        assert metrics.user_edited_fields == 1

    def test_to_dict(self):
        """Test converting to dictionary."""
        metrics = SessionMetrics(session_id="test-session")
        metrics.record_llm_call(100, 50, 500)

        result = metrics.to_dict()
        assert result["session_id"] == "test-session"
        assert result["llm"]["total_calls"] == 1


class TestMetricsCollector:
    """Test metrics collector."""

    def test_get_or_create(self):
        """Test getting or creating session metrics."""
        MetricsCollector.clear()
        metrics = MetricsCollector.get_or_create("collector_test")
        assert metrics.session_id == "collector_test"

    def test_get_existing(self):
        """Test getting existing metrics."""
        MetricsCollector.clear()
        m1 = MetricsCollector.get_or_create("existing_test")
        m2 = MetricsCollector.get_or_create("existing_test")
        assert m1 is m2

    def test_get_nonexistent(self):
        """Test getting nonexistent metrics."""
        MetricsCollector.clear()
        result = MetricsCollector.get("nonexistent_session")
        assert result is None

    def test_remove(self):
        """Test removing session metrics."""
        MetricsCollector.clear()
        MetricsCollector.get_or_create("remove_test")
        MetricsCollector.remove("remove_test")
        assert MetricsCollector.get("remove_test") is None

    def test_clear(self):
        """Test clearing all metrics."""
        MetricsCollector.get_or_create("clear_test")
        MetricsCollector.clear()
        assert MetricsCollector.get("clear_test") is None


class TestTimer:
    """Test timer context manager."""

    def test_timer_context(self):
        """Test timer as context manager."""
        with Timer("test_operation") as timer:
            time.sleep(0.01)

        assert timer.duration_ms > 0

    def test_timer_with_metadata(self):
        """Test timer with metadata."""
        with Timer("test_op", metadata={"key": "value"}) as timer:
            pass

        assert timer.metadata["key"] == "value"


class TestLogger:
    """Test logging functionality."""

    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test_module")
        assert logger is not None

    def test_logger_has_info_method(self):
        """Test logger has info method."""
        logger = get_logger("test")
        assert hasattr(logger, 'info')

    def test_logger_has_warning_method(self):
        """Test logger has warning method."""
        logger = get_logger("test")
        assert hasattr(logger, 'warning')

    def test_logger_has_error_method(self):
        """Test logger has error method."""
        logger = get_logger("test")
        assert hasattr(logger, 'error')

    def test_logger_has_debug_method(self):
        """Test logger has debug method."""
        logger = get_logger("test")
        assert hasattr(logger, 'debug')
