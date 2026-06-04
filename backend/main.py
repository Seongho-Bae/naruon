import os
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from api.auth import get_auth_context, preload_oidc_jwks
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
from api.observability import router as observability_router
from api.runner_ws import router as runner_ws_router
from api.dav import router as dav_router
from api.accounts import router as accounts_router
from api.webdav import router as webdav_router
from api.security import router as security_router
from api.data import router as data_router
from api.ai_hub import router as ai_hub_router
from core.config import settings
from core.telemetry import setup_telemetry
from services.imap_worker import ImapSyncWorker
from prometheus_fastapi_instrumentator import Instrumentator

imap_worker = ImapSyncWorker()

DISABLE_WORKERS = os.environ.get("DISABLE_BACKGROUND_WORKERS") == "1"
PRIVATE_API_DEPENDENCIES = [Depends(get_auth_context)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    preload_oidc_jwks()
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

setup_telemetry(app)

# Prometheus metrics are operational telemetry. Keep them opt-in so public
# deployments do not expose route labels and process details by default.
if settings.ENABLE_PROMETHEUS_METRICS:
    Instrumentator().instrument(app).expose(
        app, include_in_schema=False, should_gzip=True
    )

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.SECURITY_CONTENT_SECURITY_POLICY:
        response.headers["Content-Security-Policy"] = (
            settings.SECURITY_CONTENT_SECURITY_POLICY
        )
    return response

# Security enhancement: Allow configuring CORS origins for production deployments
if settings.ALLOWED_CORS_ORIGINS:
    allowed_origins = [origin.strip() for origin in settings.ALLOWED_CORS_ORIGINS.split(",") if origin.strip()]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
app.include_router(runtime_config_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(llm_providers_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(prompts_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(tasks_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(ontology_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(observability_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(runner_ws_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(dav_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(accounts_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(webdav_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(security_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(data_router, dependencies=PRIVATE_API_DEPENDENCIES)
app.include_router(ai_hub_router, dependencies=PRIVATE_API_DEPENDENCIES)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok", "message": "AI Email Client API"}
