from fastapi import FastAPI


def configure_tracing(
    app: FastAPI,
    service_name: str,
    otlp_endpoint: str | None,
    otlp_insecure: bool,
) -> bool:
    """Configure OpenTelemetry HTTP tracing when an OTLP endpoint is provided."""
    if not otlp_endpoint:
        return False
    if getattr(app.state, "otel_tracing_configured", False):
        return True

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(
        resource=Resource.create({"service.name": service_name}),
    )
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=otlp_endpoint, insecure=otlp_insecure),
        ),
    )
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=provider,
        excluded_urls="/healthz,/readyz,/metrics",
    )
    app.state.otel_tracing_configured = True
    return True
