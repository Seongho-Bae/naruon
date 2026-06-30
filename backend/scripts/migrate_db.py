from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from alembic.config import Config  # noqa: E402

from alembic import command  # noqa: E402


def alembic_config() -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    return config


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Naruon database migrations.")
    parser.add_argument(
        "revision",
        nargs="?",
        default="head",
        help="Alembic revision target. Defaults to head.",
    )
    parser.add_argument(
        "--sql",
        action="store_true",
        help="Emit SQL instead of applying migrations.",
    )
    args = parser.parse_args()

    command.upgrade(alembic_config(), args.revision, sql=args.sql)


if __name__ == "__main__":
    main()
