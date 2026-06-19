from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def test_postgres_ha_compose_exists():
    assert (_REPO_ROOT / "docker-compose.postgres-ha.yml").exists()


def test_postgres_ha_compose_allows_local_port_overrides():
    compose = (_REPO_ROOT / "docker-compose.postgres-ha.yml").read_text()

    assert "${POSTGRES_HA_PRIMARY_PORT:-5432}:5432" in compose
    assert "${POSTGRES_HA_REPLICA_PORT:-5433}:5432" in compose


def test_postgres_ha_compose_configures_replication_hba_and_replica_user():
    compose = (_REPO_ROOT / "docker-compose.postgres-ha.yml").read_text()
    init_script = (
        _REPO_ROOT / "scripts" / "postgres-ha" / "init-primary-replication.sh"
    ).read_text()

    assert "init-primary-replication.sh:/docker-entrypoint-initdb.d/010-replication-hba.sh:ro" in compose
    assert "host replication all all scram-sha-256" in init_script
    assert "gosu postgres pg_basebackup" in compose
    assert "chown -R postgres:postgres /var/lib/postgresql/data" in compose
    assert "chmod 700 /var/lib/postgresql/data" in compose
    assert "gosu postgres postgres" in compose


def test_postgres_ha_drill_script_covers_replica_readiness_and_readonly_dsn():
    drill_script = (_REPO_ROOT / "scripts" / "postgres_ha_drill.sh").read_text()

    assert "set -euo pipefail" in drill_script
    assert "docker-compose.postgres-ha.yml" in drill_script
    assert "POSTGRES_PASSWORD:-postgres" not in drill_script
    assert "POSTGRES_PASSWORD must be set" in drill_script
    assert "export POSTGRES_DB" in drill_script
    assert "export POSTGRES_USER" in drill_script
    assert "export POSTGRES_HA_PRIMARY_PORT" in drill_script
    assert "export POSTGRES_HA_REPLICA_PORT" in drill_script
    assert "pg_is_in_recovery()" in drill_script
    assert "naruon_ha_drill" in drill_script
    assert "SELECT COUNT(*)" in drill_script
    assert "READONLY_DATABASE_URL=" in drill_script
    assert "pg_stat_replication" in drill_script
    assert "db-replica" in drill_script
    assert "gosu postgres pg_ctl" in drill_script

def test_gateway_compose_exists():
    assert (_REPO_ROOT / "docker-compose.gateway.yml").exists()


def test_gateway_backend_requires_runtime_secrets():
    compose = (_REPO_ROOT / "docker-compose.gateway.yml").read_text()

    assert "DATABASE_URL: ${DATABASE_URL:?" in compose
    assert "AUTH_SESSION_HMAC_SECRET: ${AUTH_SESSION_HMAC_SECRET:?" in compose
    assert "postgresql+asyncpg://" not in compose


def test_gateway_compose_does_not_expose_management_planes():
    compose = (_REPO_ROOT / "docker-compose.gateway.yml").read_text()

    assert "--api.insecure=true" not in compose
    assert '"8080:8080"' not in compose
    assert '"8081:8080"' not in compose
    assert "KEYCLOAK_ADMIN=admin" not in compose
    assert "KEYCLOAK_ADMIN_PASSWORD=admin" not in compose
    assert "KEYCLOAK_ADMIN=${KEYCLOAK_ADMIN:?" in compose
    assert "KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD:?" in compose
