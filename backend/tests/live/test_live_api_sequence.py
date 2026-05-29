"""Live HTTP smoke tests for Docker-built release candidates."""

from __future__ import annotations

import json
import http.client
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


def read_json(url: str, *, attempts: int = 12) -> dict[str, Any]:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            parsed_url = urlsplit(url)
            if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
                raise ValueError("Only HTTP and HTTPS endpoint URLs are allowed")
            connection_cls = (
                http.client.HTTPSConnection
                if parsed_url.scheme == "https"
                else http.client.HTTPConnection
            )
            request_path = parsed_url.path or "/"
            if parsed_url.query:
                request_path = f"{request_path}?{parsed_url.query}"
            connection = connection_cls(
                parsed_url.hostname,
                parsed_url.port,
                timeout=5,
            )
            try:
                connection.request("GET", request_path)
                response = connection.getresponse()
                assert response.status == 200
                return json.loads(response.read().decode("utf-8"))
            finally:
                connection.close()
        except (OSError, http.client.HTTPException) as exc:
            last_error = exc
            time.sleep(1)
    raise AssertionError(f"live endpoint unavailable: {url}") from last_error


def test_live_api_sequence_uses_real_http(live_base_url: str) -> None:
    for _ in range(12):
        inbox = read_json(f"{live_base_url}/api/emails")
        subjects = {item.get("subject") for item in inbox["emails"]}
        if "Live E2E Release" in subjects:
            return
        time.sleep(1)
    raise AssertionError("seeded live email was not observed in time")


def test_live_harness_forbids_in_process_clients_and_mocks() -> None:
    live_root = Path(__file__).resolve().parent
    forbidden_terms = ("Test" "Client", "ASGI" "Transport", "unittest" ".mock")
    offenders: list[str] = []
    for path in sorted(live_root.glob("*.py")):
        if path.name == "test_live_api_sequence.py":
            continue
        source = path.read_text(encoding="utf-8")
        offenders.extend(term for term in forbidden_terms if term in source)

    assert offenders == []


def test_live_harness_avoids_broad_url_opener_pattern() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    unsafe_terms = ("urllib" ".request", "url" "open")

    for unsafe_term in unsafe_terms:
        assert unsafe_term not in source
