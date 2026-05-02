#!/usr/bin/env python3
"""Create a local signed bearer-token value for the AI Email Client API."""

from __future__ import annotations

import argparse
import datetime
import os
import sys
import uuid

import jwt


def create_token(user_id: str, secret: str, ttl_seconds: int) -> str:
    """Create a PyJWT HMAC-signed token compatible with backend.api.auth."""
    now = datetime.datetime.now(datetime.timezone.utc)
    return jwt.encode(
        {
            "sub": user_id,
            "iat": now,
            "exp": now + datetime.timedelta(seconds=ttl_seconds),
            "jti": uuid.uuid4().hex,
        },
        secret,
        algorithm="HS256",
    )


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
