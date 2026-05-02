#!/usr/bin/env python3
"""Create a local signed bearer-token value for the AI Email Client API."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import time


def base64url_encode(data: bytes) -> str:
    """Return unpadded base64url text for token segments."""
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def create_token(user_id: str, secret: str, ttl_seconds: int) -> str:
    """Create an HMAC-signed token compatible with backend.api.auth."""
    payload = json.dumps(
        {"sub": user_id, "exp": int(time.time()) + ttl_seconds},
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    encoded_payload = base64url_encode(payload)
    signature = hmac.new(
        secret.encode(), encoded_payload.encode(), hashlib.sha256
    ).digest()
    return f"{encoded_payload}.{base64url_encode(signature)}"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("user_id", help="User ID to place in the token subject")
    parser.add_argument(
        "--ttl-seconds",
        type=int,
        default=86_400,
        help="Token lifetime in seconds (default: 86400)",
    )
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint."""
    args = parse_args()
    secret = os.environ.get("AUTH_TOKEN_SECRET", "").strip()
    if not secret:
        print("AUTH_TOKEN_SECRET is required", file=sys.stderr)
        return 2
    if not args.user_id.strip():
        print("user_id is required", file=sys.stderr)
        return 2

    print(create_token(args.user_id, secret, args.ttl_seconds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
