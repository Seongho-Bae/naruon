"""Seed deterministic data for the live Docker E2E stack."""

from __future__ import annotations

import asyncio
import datetime as dt

from sqlalchemy import delete

from db.models import Email
from db.session import AsyncSessionLocal


THREAD_ID = "<live-e2e-root@example.test>"
MESSAGE_IDS = [
    "<live-e2e-root@example.test>",
    "<live-e2e-reply@example.test>",
]


async def seed_live_data() -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Email).where(Email.message_id.in_(MESSAGE_IDS)))
        session.add_all(
            [
                Email(
                    message_id=MESSAGE_IDS[0],
                    thread_id=THREAD_ID,
                    sender="ops@example.test",
                    recipients="swe@example.test",
                    subject="Live E2E Release",
                    date=dt.datetime(2026, 5, 11, 12, 0, tzinfo=dt.timezone.utc),
                    body="Root live release evidence message.",
                    embedding=[0.0] * 1536,
                ),
                Email(
                    message_id=MESSAGE_IDS[1],
                    thread_id=THREAD_ID,
                    sender="swe@example.test",
                    recipients="ops@example.test",
                    subject="Live E2E Release",
                    in_reply_to=MESSAGE_IDS[0],
                    references=MESSAGE_IDS[0],
                    date=dt.datetime(2026, 5, 11, 12, 1, tzinfo=dt.timezone.utc),
                    body="Reply live release evidence message.",
                    embedding=[0.0] * 1536,
                ),
            ]
        )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_live_data())
