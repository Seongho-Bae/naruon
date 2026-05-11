#!/usr/bin/env python3
"""Fail release log scans except for documented upstream startup noise."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from typing import Iterable


FORBIDDEN_LOG_RE = re.compile(
    r"\b(?:warning|warn|deprecated|notice|fatal|denied|unable)\b", re.IGNORECASE
)


@dataclass(frozen=True)
class AllowedLogPattern:
    """Documented warning-class log line that remains acceptable."""

    component: str
    version: str
    rationale: str
    pattern: re.Pattern[str]


ALLOWLIST: tuple[AllowedLogPattern, ...] = (
    AllowedLogPattern(
        component="nginx",
        version="1.27.x-alpine",
        rationale="Nginx emits notice-level worker startup lines before serving traffic.",
        pattern=re.compile(
            r"nginx.*\[notice\].*(using the .* event method|nginx/|built by gcc|"
            r"OS:|getrlimit\(RLIMIT_NOFILE\)|start worker processes|"
            r"start worker process \d+)",
            re.IGNORECASE,
        ),
    ),
    AllowedLogPattern(
        component="postgres",
        version="pgvector/pg16 local Docker",
        rationale="Host-local Netdata PostgreSQL discovery can probe isolated test containers.",
        pattern=re.compile(
            r"db-1\s+\| .*FATAL:\s+password authentication failed for user \"netdata\"",
            re.IGNORECASE,
        ),
    ),
    AllowedLogPattern(
        component="grafana",
        version="11.5.x",
        rationale="Grafana logs idempotent migrations already applied on startup.",
        pattern=re.compile(
            r"grafana.*level=warn.*Skipping migration: Already executed, "
            r"but not recorded in migration log",
            re.IGNORECASE,
        ),
    ),
    AllowedLogPattern(
        component="grafana",
        version="11.5.x",
        rationale="Grafana OSS may not include optional bundled plugin files.",
        pattern=re.compile(
            r"grafana.*level=warn.*Skipping finding plugins as directory does not exist.*"
            r"/usr/share/grafana/plugins-bundled",
            re.IGNORECASE,
        ),
    ),
    AllowedLogPattern(
        component="grafana",
        version="11.5.x",
        rationale="Anonymous local startup falls back before login.",
        pattern=re.compile(
            r"grafana.*level=warn.*User does not belong to a user or service account "
            r"namespace, using 0 as user ID",
            re.IGNORECASE,
        ),
    ),
    AllowedLogPattern(
        component="grafana",
        version="11.5.x",
        rationale="Grafana may double-register internal metrics at startup.",
        pattern=re.compile(
            r"grafana.*level=warn.*failed to register storage metrics.*"
            r"duplicate metrics collector registration attempted",
            re.IGNORECASE,
        ),
    ),
    AllowedLogPattern(
        component="tempo",
        version="2.7.x",
        rationale="Tempo self-scans its local blocks directory during WAL replay.",
        pattern=re.compile(
            r"tempo.*level=warn.*unowned file entry ignored during wal replay.*file=blocks",
            re.IGNORECASE,
        ),
    ),
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line flags for the compose log scanner."""

    parser = argparse.ArgumentParser(
        description=(
            "Scan Docker Compose logs from stdin and fail on warning-class lines "
            "unless they match documented upstream startup noise."
        )
    )
    return parser.parse_args(argv)


def scan_lines(lines: Iterable[str]) -> tuple[list[str], list[str]]:
    """Return unexpected forbidden lines and allowed warning-class lines."""

    unexpected: list[str] = []
    allowed: list[str] = []
    for line in lines:
        if not FORBIDDEN_LOG_RE.search(line):
            continue
        if any(item.pattern.search(line) for item in ALLOWLIST):
            allowed.append(line)
            continue
        unexpected.append(line)
    return unexpected, allowed


def main(argv: list[str] | None = None) -> int:
    """Scan stdin and return a shell-friendly status code."""

    parse_args(sys.argv[1:] if argv is None else argv)
    unexpected, allowed = scan_lines(sys.stdin.read().splitlines())
    if unexpected:
        print("FAIL compose log policy: unexpected warning-class lines", file=sys.stderr)
        for line in unexpected[:80]:
            print(line, file=sys.stderr)
        print(f"unexpected_count={len(unexpected)}", file=sys.stderr)
        print(f"allowed_count={len(allowed)}", file=sys.stderr)
        return 1
    print(f"PASS compose log policy: allowed_count={len(allowed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
