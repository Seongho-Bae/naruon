from __future__ import annotations

import argparse
from pathlib import Path

from alembic import command
from alembic.config import Config


def alembic_config() -> Config:
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
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
