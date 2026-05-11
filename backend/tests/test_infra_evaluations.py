from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def test_postgres_ha_compose_exists():
    assert (_REPO_ROOT / "docker-compose.postgres-ha.yml").exists()

def test_gateway_compose_exists():
    assert (_REPO_ROOT / "docker-compose.gateway.yml").exists()
