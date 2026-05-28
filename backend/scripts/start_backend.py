import os
import sys
from pathlib import Path

REQUIRED_ENV_VARS = ("DATABASE_URL", "AUTH_SESSION_HMAC_SECRET")
DEFAULT_ENV_FILE_CANDIDATES = ("~/.env", "../.env", ".env")
DEFAULT_BIND_HOST = "127.0.0.1"
DEFAULT_BIND_PORT = "8000"
CONFIG_ERROR_EXIT_CODE = 78


def _candidate_env_files() -> list[Path]:
    candidates = [
        os.environ.get("NARUON_BACKEND_ENV_FILE"),
        os.environ.get("NARUON_ENV_FILE"),
        *DEFAULT_ENV_FILE_CANDIDATES,
    ]
    paths: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        try:
            key = str(path.resolve(strict=False))
        except OSError:
            key = str(path)
        if key in seen:
            continue
        seen.add(key)
        paths.append(path)
    return paths


def _non_empty_env_keys(path: Path) -> set[str]:
    if not path.is_file():
        return set()

    keys: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").lstrip()
        key, raw_value = line.split("=", 1)
        normalized_value = raw_value.strip().strip("'\"")
        if key.strip() and normalized_value:
            keys.add(key.strip())
    return keys


def missing_required_env() -> list[str]:
    env_file_keys: set[str] = set()
    for env_file in _candidate_env_files():
        env_file_keys.update(_non_empty_env_keys(env_file))

    return [
        name
        for name in REQUIRED_ENV_VARS
        if not os.environ.get(name) and name not in env_file_keys
    ]


def main() -> int:
    missing = missing_required_env()
    if missing:
        sys.stderr.write(
            "Missing required backend runtime env: "
            + ", ".join(missing)
            + ".\n"
        )
        sys.stderr.write(
            "Inject them with Docker/Compose/Kubernetes secrets, or mount a "
            "backend-only env file and point NARUON_ENV_FILE or "
            "NARUON_BACKEND_ENV_FILE at it. Code defaults are intentionally "
            "not provided.\n"
        )
        return CONFIG_ERROR_EXIT_CODE

    if os.environ.get("NARUON_STARTUP_CHECK_ONLY") == "1":
        return 0

    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.environ.get("BACKEND_BIND_HOST", DEFAULT_BIND_HOST),
        port=int(os.environ.get("BACKEND_BIND_PORT", DEFAULT_BIND_PORT)),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
