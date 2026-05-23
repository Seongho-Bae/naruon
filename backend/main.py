import os
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth import get_auth_context
from api.search import router as search_router
from api.llm import router as llm_router
from api.calendar import router as calendar_router
from api.network import router as network_router
from api.emails import router as emails_router
from api.runner_config import router as runner_config_router
from api.tenant_config import router as tenant_config_router
from api.runtime_config import router as runtime_config_router
from api.llm_providers import router as llm_providers_router
from api.prompts import router as prompts_router
from api.tasks import router as tasks_router
from api.ontology import router as ontology_router
from api.runner_ws import router as runner_ws_router
from services.imap_worker import ImapSyncWorker
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

imap_worker = ImapSyncWorker()

DISABLE_WORKERS = os.environ.get("DISABLE_BACKGROUND_WORKERS") == "1"
PRIVATE_API_DEPENDENCIES = [Depends(get_auth_context)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not DISABLE_WORKERS:
        await imap_worker.start()
    yield
    if not DISABLE_WORKERS:
        await imap_worker.stop()


app = FastAPI(
    title="Naruon Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# OpenTelemetry Tracing Setup (if enabled)
if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME

    resource = Resource(attributes={SERVICE_NAME: "naruon-backend"})

    trace_provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter())
    trace_provider.add_span_processor(processor)
    trace.set_tracer_provider(trace_provider)

# Instrument Prometheus Metrics
Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)

# Instrument OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(llm_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(calendar_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(network_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(emails_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(runner_config_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(tenant_config_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(runtime_config_router)
app.include_router(llm_providers_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(prompts_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(tasks_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(ontology_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(runner_ws_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok", "message": "AI Email Client API"}
