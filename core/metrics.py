"""Prometheus metrics for FastAPI"""
import os
from loguru import logger


_instrumentator = None


def setup_prometheus(app):
    """Setup Prometheus metrics instrumentation and /metrics endpoint"""
    global _instrumentator
    if os.getenv("ENABLE_METRICS", "true").lower() != "true":
        logger.info("[Metrics] Prometheus disabled")
        return
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from fastapi import Response

        _instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            should_respect_env_var=False,
            excluded_handlers=["/health", "/metrics"],
            env_var_name="ENABLE_METRICS",
        )
        _instrumentator.instrument(app)

        # Manual /metrics endpoint (more reliable than expose())
        @app.get("/metrics", include_in_schema=False)
        async def metrics():
            return Response(
                content=generate_latest(),
                media_type=CONTENT_TYPE_LATEST,
            )

        logger.info("[Metrics] Prometheus /metrics endpoint enabled")
    except ImportError:
        logger.warning("[Metrics] prometheus-fastapi-instrumentator not installed")
    except Exception as e:
        logger.error(f"[Metrics] Setup failed: {e}")
