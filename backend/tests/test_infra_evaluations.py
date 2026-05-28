from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def test_postgres_ha_compose_exists():
    assert (_REPO_ROOT / "docker-compose.postgres-ha.yml").exists()

def test_gateway_compose_exists():
    assert (_REPO_ROOT / "docker-compose.gateway.yml").exists()


def test_gateway_backend_requires_runtime_secrets():
    compose = (_REPO_ROOT / "docker-compose.gateway.yml").read_text()

    assert "DATABASE_URL: ${DATABASE_URL:?" in compose
    assert "AUTH_SESSION_HMAC_SECRET: ${AUTH_SESSION_HMAC_SECRET:?" in compose
    assert "postgresql+asyncpg://" not in compose
