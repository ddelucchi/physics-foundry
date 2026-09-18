"""Optional instrumentation for Physics Foundry orchestration.

Observability is deliberately downstream of execution semantics. Safety-critical
process execution lives in ``core.processes`` and must not depend on tracing,
metrics exporters, Sentry, or GPU monitoring packages.
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional

from prometheus_client import Counter, Gauge, Histogram

from .processes import ProcessTimeoutError, process_manager

logger = logging.getLogger(__name__)


pipeline_operations_total = Counter(
    "pipeline_operations_total",
    "Total pipeline operations",
    ["operation", "status"],
)

operation_duration_seconds = Histogram(
    "operation_duration_seconds",
    "Time spent on operations",
    ["operation"],
)

gpu_memory_usage = Gauge(
    "gpu_memory_usage_bytes",
    "GPU memory usage in bytes",
    ["device"],
)

retry_attempts_total = Counter(
    "retry_attempts_total",
    "Total retry attempts",
    ["operation", "reason"],
)


class RetryableOperation:
    """Dependency-light retry adapter for explicitly retryable integrations."""

    @staticmethod
    def with_backoff(
        max_attempts: int = 3,
        min_wait: float = 1.0,
        max_wait: float = 10.0,
        exceptions: tuple = (Exception,),
    ):
        def decorator(func):
            if inspect.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    delay = min_wait
                    for attempt in range(1, max_attempts + 1):
                        try:
                            return await func(*args, **kwargs)
                        except exceptions as exc:
                            if attempt >= max_attempts:
                                raise
                            retry_attempts_total.labels(
                                operation=func.__name__,
                                reason=type(exc).__name__,
                            ).inc()
                            logger.warning(
                                "Retrying %s after %s (attempt %s/%s)",
                                func.__name__,
                                type(exc).__name__,
                                attempt,
                                max_attempts,
                            )
                            await asyncio.sleep(delay)
                            delay = min(max_wait, max(min_wait, delay * 2))

                return async_wrapper

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                import time

                delay = min_wait
                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as exc:
                        if attempt >= max_attempts:
                            raise
                        retry_attempts_total.labels(
                            operation=func.__name__,
                            reason=type(exc).__name__,
                        ).inc()
                        logger.warning(
                            "Retrying %s after %s (attempt %s/%s)",
                            func.__name__,
                            type(exc).__name__,
                            attempt,
                            max_attempts,
                        )
                        time.sleep(delay)
                        delay = min(max_wait, max(min_wait, delay * 2))

            return sync_wrapper

        return decorator


class ObservabilityManager:
    """Configure optional tracing and error reporting without blocking service boot."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tracer = None
        self.tracing_configured = False
        self.sentry_configured = False

    def setup_tracing(self, jaeger_endpoint: Optional[str] = None) -> bool:
        """Configure Jaeger export only when the SDK and endpoint both exist."""

        if not jaeger_endpoint:
            logger.info("Jaeger endpoint not configured; tracing export disabled")
            return False

        try:
            import opentelemetry.trace as trace
            from opentelemetry.exporter.jaeger.thrift import JaegerExporter
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            provider = TracerProvider()
            exporter = JaegerExporter(collector_endpoint=jaeger_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            self.tracer = trace.get_tracer(__name__)
            self.tracing_configured = True
            logger.info("OpenTelemetry tracing configured for %s", jaeger_endpoint)
            return True
        except ImportError:
            logger.warning("OpenTelemetry/Jaeger packages unavailable; tracing disabled")
        except Exception:
            logger.exception("Tracing setup failed; continuing without tracing export")

        self.tracer = None
        self.tracing_configured = False
        return False

    def setup_error_tracking(self, dsn: Optional[str] = None) -> bool:
        """Configure Sentry only when the SDK and DSN are both available."""

        if not dsn:
            return False

        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration

            sentry_sdk.init(
                dsn=dsn,
                integrations=[FastApiIntegration()],
                traces_sample_rate=0.1,
                environment=self.config.get("environment", "development"),
            )
            self.sentry_configured = True
            logger.info("Sentry error tracking configured")
            return True
        except ImportError:
            logger.warning("Sentry SDK unavailable; remote error tracking disabled")
        except Exception:
            logger.exception("Sentry setup failed; continuing without remote error tracking")

        self.sentry_configured = False
        return False

    @asynccontextmanager
    async def trace_operation(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Any, None]:
        """Trace an operation when tracing exists; otherwise act as a no-op context."""

        if self.tracer is None:
            yield None
            return

        with self.tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            yield span


class SystemMonitor:
    """Best-effort GPU-memory metric collector."""

    def __init__(self) -> None:
        self.monitoring = False

    async def start_monitoring(self, interval: float = 2.0) -> None:
        """Collect optional NVIDIA memory metrics until stopped."""

        if self.monitoring:
            return

        self.monitoring = True
        while self.monitoring:
            try:
                import pynvml

                pynvml.nvmlInit()
                try:
                    for index in range(pynvml.nvmlDeviceGetCount()):
                        handle = pynvml.nvmlDeviceGetHandleByIndex(index)
                        memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        gpu_memory_usage.labels(device=f"gpu_{index}").set(memory.used)
                finally:
                    try:
                        pynvml.nvmlShutdown()
                    except Exception:
                        pass
            except ImportError:
                pass
            except Exception as exc:
                logger.debug("GPU monitoring unavailable: %s", exc)

            await asyncio.sleep(interval)

    def stop_monitoring(self) -> None:
        self.monitoring = False


observability_manager = ObservabilityManager({})
system_monitor = SystemMonitor()


def setup_observability_stack(
    prometheus_port: int = 9090,
    jaeger_endpoint: Optional[str] = None,
    sentry_dsn: Optional[str] = None,
) -> Dict[str, bool]:
    """Configure optional exporters and report what was actually enabled.

    Prometheus metrics are exposed by the FastAPI ``/metrics`` route; this
    function intentionally does not start a second HTTP server or background
    system-monitor task.
    """

    del prometheus_port
    return {
        "prometheus_route": True,
        "tracing": observability_manager.setup_tracing(jaeger_endpoint),
        "sentry": observability_manager.setup_error_tracking(sentry_dsn),
    }


__all__ = [
    "ProcessTimeoutError",
    "RetryableOperation",
    "observability_manager",
    "operation_duration_seconds",
    "pipeline_operations_total",
    "process_manager",
    "retry_attempts_total",
    "setup_observability_stack",
    "system_monitor",
]
