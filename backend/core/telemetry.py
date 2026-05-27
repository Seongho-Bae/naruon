import logging
import os
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

logger = logging.getLogger(__name__)
_telemetry_configured = False


def _env_flag(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def setup_telemetry(app: FastAPI):
    global _telemetry_configured

    if _telemetry_configured:
        logger.debug("OpenTelemetry instrumentation is already configured.")
        return

    # Only set up tracing when ENABLE_OTEL is true and an OTLP endpoint is set.
    enable_otel = _env_flag("ENABLE_OTEL")
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    if not enable_otel or not otel_endpoint:
        logger.info("OpenTelemetry is disabled.")
        return

    otlp_insecure = _env_flag("OTEL_EXPORTER_OTLP_INSECURE")

    try:
        logger.info("Setting up OpenTelemetry export.")
        resource = Resource(attributes={SERVICE_NAME: "naruon-backend"})

        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        otlp_exporter = OTLPSpanExporter(
            endpoint=otel_endpoint,
            insecure=otlp_insecure,
        )
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)

        FastAPIInstrumentor.instrument_app(app)
        _telemetry_configured = True
        logger.info("OpenTelemetry instrumentation completed successfully.")
    except Exception:
        logger.exception("OpenTelemetry setup failed; continuing without tracing.")
