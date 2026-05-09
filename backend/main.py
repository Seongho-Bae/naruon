from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from api.search import router as search_router
from api.llm import router as llm_router
from api.calendar import router as calendar_router
from api.network import router as network_router
from api.emails import router as emails_router
from api.tenant_config import router as tenant_config_router
from core.config import settings
from core.observability import configure_tracing
from db.session import engine
from services.imap_worker import ImapSyncWorker

imap_worker = ImapSyncWorker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_started = False
    if (
        settings.ENABLE_API_BACKGROUND_WORKERS
        and not settings.DISABLE_BACKGROUND_WORKERS
    ):
        await imap_worker.start()
        worker_started = True
    try:
        yield
    finally:
        if worker_started:
            await imap_worker.stop()


app = FastAPI(title="AI Email Client API", lifespan=lifespan)

app.include_router(search_router)
app.include_router(llm_router)
app.include_router(calendar_router)
app.include_router(network_router)
app.include_router(emails_router)
app.include_router(tenant_config_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

configure_tracing(
    app,
    settings.OTEL_SERVICE_NAME,
    settings.OTEL_EXPORTER_OTLP_ENDPOINT,
    settings.OTEL_EXPORTER_OTLP_INSECURE,
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok", "message": "AI Email Client API"}


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict[str, str]:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is not ready") from exc
    return {"status": "ready"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
