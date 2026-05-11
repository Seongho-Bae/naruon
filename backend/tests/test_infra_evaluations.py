import pytest
from pathlib import Path

def test_postgres_ha_compose_exists():
    assert Path("docker-compose.postgres-ha.yml").exists()

def test_gateway_compose_exists():
    assert Path("docker-compose.gateway.yml").exists()
