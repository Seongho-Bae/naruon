from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.search import router as search_router
from api.auth import router as auth_router
from api.llm import router as llm_router
from api.calendar import router as calendar_router
from api.network import router as network_router
from api.emails import router as emails_router
from api.tenant_config import router as tenant_config_router
from services.imap_worker import ImapSyncWorker

imap_worker = ImapSyncWorker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await imap_worker.start()
    yield
    await imap_worker.stop()


app = FastAPI(title="AI Email Client API", lifespan=lifespan)

app.include_router(auth_router)
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


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok", "message": "AI Email Client API"}
