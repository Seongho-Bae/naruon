from pathlib import Path


def test_observability_compose_file_exists():
    assert Path("../docker-compose.observability.yml").exists()


def test_observability_provisioning_exists():
    assert Path(
        "../observability/grafana/provisioning/datasources/datasources.yaml"
    ).exists()
    assert Path("../observability/prometheus.yml").exists()
    assert Path("../observability/tempo.yaml").exists()


def test_backend_exposes_metrics_endpoint():
    from main import app
    from fastapi.testclient import TestClient
    from tests.auth_helpers import auth_headers

    with TestClient(app, headers=auth_headers("testuser")) as client:
        # Before instrumentation, it might be 404, but after it should be 200
        response = client.get("/metrics")
        # Ensure it is added as part of the APM implementation
        assert response.status_code == 200
        assert "python_info" in response.text or "process_" in response.text
