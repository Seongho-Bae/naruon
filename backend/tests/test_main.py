from fastapi.testclient import TestClient
import main
from main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "AI Email Client API"}


def test_healthz_reports_application_liveness_without_touching_dependencies():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_exposes_prometheus_text_format():
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "python_info" in response.text


def test_readyz_reports_database_readiness(monkeypatch):
    class ReadyConnection:
        async def execute(self, _statement):
            return None

    class ReadyContext:
        async def __aenter__(self):
            return ReadyConnection()

        async def __aexit__(self, exc_type, exc, traceback):
            return False

    class ReadyEngine:
        def connect(self):
            return ReadyContext()

    monkeypatch.setattr(main, "engine", ReadyEngine())

    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readyz_reports_database_unready_without_leaking_exception(monkeypatch):
    class UnreadyContext:
        async def __aenter__(self):
            raise RuntimeError("database password details")

        async def __aexit__(self, exc_type, exc, traceback):
            return False

    class UnreadyEngine:
        def connect(self):
            return UnreadyContext()

    monkeypatch.setattr(main, "engine", UnreadyEngine())

    response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is not ready"}
