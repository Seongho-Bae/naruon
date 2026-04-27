from fastapi import FastAPI

app = FastAPI(title="AI Email Client API")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI Email Client API"}