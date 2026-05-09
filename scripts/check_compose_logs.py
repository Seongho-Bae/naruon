#!/usr/bin/env python3
"""Fail release log scans except for documented upstream startup noise."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from typing import Iterable


FORBIDDEN_LOG_RE = re.compile(
    r"\b(?:warning|warn|deprecated|notice|fatal|denied|unable)\b", re.IGNORECASE
)


@dataclass(frozen=True)
class AllowedLogPattern:
    component: str
    version: str
    rationale: str
    pattern: re.Pattern[str]


ALLOWLIST: tuple[AllowedLogPattern, ...] = (
    AllowedLogPattern(
        component="grafana",
        version="11.5.x",
        rationale="Grafana logs idempotent migrations already applied on fresh local startup.",
        pattern=re.compile(
            r"grafana.*level=warn.*Skipping migration: Already executed, "
            r"but not recorded in migration log",
            re.IGNORECASE,
        ),
    ),
    AllowedLogPattern(
        component="grafana",
        version="11.5.x",
        rationale="Grafana OSS image may not include the optional bundled plugin directory.",
        pattern=re.compile(
            r"grafana.*level=warn.*Skipping finding plugins as directory does not exist.*"
            r"/usr/share/grafana/plugins-bundled",
            re.IGNORECASE,
        ),
    ),
    AllowedLogPattern(
        component="grafana",
        version="11.5.x",
        rationale="Anonymous local startup falls back to namespace id 0 before login.",
        pattern=re.compile(
            r"grafana.*level=warn.*User does not belong to a user or service account "
            r"namespace, using 0 as user ID",
            re.IGNORECASE,
        ),
    ),
    AllowedLogPattern(
        component="grafana",
        version="11.5.x",
        rationale="Grafana 11.5.x may double-register internal storage metrics at startup.",
        pattern=re.compile(
            r"grafana.*level=warn.*failed to register storage metrics.*"
            r"duplicate metrics collector registration attempted",
            re.IGNORECASE,
        ),
    ),
    AllowedLogPattern(
        component="tempo",
        version="2.7.x",
        rationale="Tempo 2.7.x self-scans its local blocks directory during WAL replay.",
        pattern=re.compile(
            r"tempo.*level=warn.*unowned file entry ignored during wal replay.*file=blocks",
            re.IGNORECASE,
        ),
    ),
)


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


def main() -> int:
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
