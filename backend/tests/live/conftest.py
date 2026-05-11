"""Pytest options for live Docker E2E tests."""

from __future__ import annotations

import os

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--live-base-url",
        action="store",
        default=None,
        help="Base URL for the already-running live HTTP stack.",
    )


@pytest.fixture
def live_base_url(request: pytest.FixtureRequest) -> str:
    value = request.config.getoption("--live-base-url") or os.environ.get(
        "LIVE_BASE_URL"
    )
    if not value:
        pytest.skip("live tests require --live-base-url or LIVE_BASE_URL")
    return str(value).rstrip("/")
