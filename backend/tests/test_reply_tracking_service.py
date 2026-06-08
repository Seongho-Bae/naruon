import datetime

from db.models import Email
from services.reply_tracking_service import thread_reply_candidate


USER_ADDRESSES = {"me@example.com"}
BASE_TIME = datetime.datetime(2026, 5, 28, 9, 0, tzinfo=datetime.timezone.utc)


def make_email(
    message_id: str,
    *,
    sender: str,
    recipients: str,
    minutes: int,
    body: str = "Could you please reply?",
) -> Email:
    return Email(
        user_id="user_1",
        organization_id="org_1",
        message_id=message_id,
        thread_id="thread_1",
        sender=sender,
        recipients=recipients,
        subject="Reply tracking",
        date=BASE_TIME + datetime.timedelta(minutes=minutes),
        body=body,
    )


def test_thread_reply_candidate_returns_latest_unanswered_sent_message():
    older_sent = make_email(
        "sent_older",
        sender="Me <me@example.com>",
        recipients="client@example.com",
        minutes=0,
    )
    external_reply = make_email(
        "external_reply",
        sender="client@example.com",
        recipients="me@example.com",
        minutes=5,
        body="Thanks, received.",
    )
    latest_sent = make_email(
        "sent_latest",
        sender="me@example.com",
        recipients="client@example.com",
        minutes=10,
    )

    candidate = thread_reply_candidate(
        [latest_sent, older_sent, external_reply],
        USER_ADDRESSES,
    )

    assert candidate is latest_sent


def test_thread_reply_candidate_ignores_sent_message_with_later_external_reply():
    sent_message = make_email(
        "sent_needs_reply",
        sender="me@example.com",
        recipients="client@example.com",
        minutes=0,
    )
    later_external_reply = make_email(
        "external_later",
        sender="client@example.com",
        recipients="me@example.com",
        minutes=1,
        body="I will handle it.",
    )

    assert (
        thread_reply_candidate([sent_message, later_external_reply], USER_ADDRESSES)
        is None
    )


def test_thread_reply_candidate_ignores_self_sent_knowledge_messages():
    self_sent = make_email(
        "self_sent",
        sender="Me <me@example.com>",
        recipients="me@example.com",
        minutes=0,
    )

    assert thread_reply_candidate([self_sent], USER_ADDRESSES) is None


def test_thread_reply_candidate_preserves_strict_later_reply_boundary():
    sent_message = make_email(
        "sent_same_time",
        sender="me@example.com",
        recipients="client@example.com",
        minutes=0,
    )
    same_time_external = make_email(
        "external_same_time",
        sender="client@example.com",
        recipients="me@example.com",
        minutes=0,
        body="Crossed in transit.",
    )

    candidate = thread_reply_candidate(
        [same_time_external, sent_message],
        USER_ADDRESSES,
    )

    assert candidate is sent_message
