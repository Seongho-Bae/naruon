import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
from api.execution_items import router as execution_items_router
from api.mailbox_accounts import router as mailbox_accounts_router
from services.imap_worker import ImapSyncWorker
from services.pop3_worker import Pop3SyncWorker
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

imap_worker = ImapSyncWorker()
pop3_worker = Pop3SyncWorker()

DISABLE_WORKERS = os.environ.get("DISABLE_BACKGROUND_WORKERS") == "1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if DISABLE_WORKERS:
        yield
        return

    imap_started = False
    pop3_started = False
    try:
        await imap_worker.start()
        imap_started = True
        await pop3_worker.start()
        pop3_started = True
        yield
    finally:
        if pop3_started:
            await pop3_worker.stop()
        if imap_started:
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

app.include_router(search_router)
app.include_router(llm_router)
app.include_router(calendar_router)
app.include_router(network_router)
app.include_router(emails_router)
app.include_router(runner_config_router)
app.include_router(tenant_config_router)
app.include_router(runtime_config_router)
app.include_router(llm_providers_router)
app.include_router(prompts_router)
app.include_router(execution_items_router)
app.include_router(mailbox_accounts_router)


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
