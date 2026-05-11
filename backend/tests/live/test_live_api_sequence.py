"""Live HTTP smoke tests for Docker-built release candidates."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def read_json(url: str, *, attempts: int = 12) -> dict[str, Any]:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                assert response.status == 200
                return json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc
            time.sleep(1)
    raise AssertionError(f"live endpoint unavailable: {url}") from last_error


def test_live_api_sequence_uses_real_http(live_base_url: str) -> None:
    inbox = read_json(f"{live_base_url}/api/emails")
    subjects = {item.get("subject") for item in inbox["emails"]}
    assert "Live E2E Release" in subjects


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
