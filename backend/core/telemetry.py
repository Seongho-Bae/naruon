import logging
import os
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

logger = logging.getLogger(__name__)

def setup_telemetry(app: FastAPI):
    # Only setup if OTEL is enabled or endpoint is provided
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    enable_otel = os.getenv("ENABLE_OTEL", "true").lower() == "true"
    
    if not enable_otel:
        logger.info("OpenTelemetry is disabled via ENABLE_OTEL.")
        return

    logger.info(f"Setting up OpenTelemetry to export to {otel_endpoint}")
    
    # Configure Tracer Provider with Resource Info
    resource = Resource(attributes={
        SERVICE_NAME: "naruon-backend"
    })
    
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    # Configure OTLP Exporter
    otlp_exporter = OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    logger.info("OpenTelemetry instrumentation completed successfully.")
