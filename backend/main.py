from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.search import router as search_router
from api.llm import router as llm_router
from api.calendar import router as calendar_router
from api.network import router as network_router

app = FastAPI(title="AI Email Client API")

app.include_router(search_router)
app.include_router(llm_router)
app.include_router(calendar_router)
app.include_router(network_router)

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