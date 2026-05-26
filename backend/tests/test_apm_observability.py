from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent

def test_observability_compose_file_exists():
    assert (ROOT_DIR / "docker-compose.infra.yml").exists()


def test_observability_provisioning_exists():
    assert (
        ROOT_DIR / "observability/grafana/provisioning/datasources/datasources.yaml"
    ).exists()
    assert (ROOT_DIR / "observability/prometheus.yml").exists()
    assert (ROOT_DIR / "observability/tempo.yaml").exists()


def test_backend_metrics_endpoint_is_disabled_by_default():
    from main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/metrics")
        assert response.status_code == 404


def test_metrics_exposure_requires_explicit_environment_gate():
    main_source = (ROOT_DIR / "backend/main.py").read_text()

    assert "ENABLE_PROMETHEUS_METRICS" in main_source
    assert "Instrumentator().instrument(app).expose" in main_source
