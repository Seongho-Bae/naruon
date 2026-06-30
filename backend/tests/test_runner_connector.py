import json
from unittest.mock import AsyncMock

import pytest

from runner.connector import SelfHostedConnector


@pytest.mark.asyncio
async def test_handle_message_dispatches_fetch_imap():
    async def fetch_imap_adapter(payload):
        assert payload["account"] == "mailbox-1"
        return {
            "status": "success",
            "messages_imported": 2,
            "provider_write_executed": False,
        }

    connector = SelfHostedConnector(
        "ws://gateway.example/api/runner/ws",
        "token",
        imap_fetch_handler=fetch_imap_adapter,
    )
    original_handler = connector._handle_fetch_imap
    connector._handle_fetch_imap = AsyncMock(wraps=original_handler)
    connector.send_response = AsyncMock()

    await connector.handle_message(
        json.dumps(
            {
                "action": "fetch_imap",
                "account": "mailbox-1",
                "request_id": "runner_req_1",
            }
        )
    )

    connector._handle_fetch_imap.assert_awaited_once()
    connector.send_response.assert_awaited_once_with(
        {
            "status": "success",
            "action": "fetch_imap",
            "protocol": "IMAP",
            "account": "mailbox-1",
            "request_id": "runner_req_1",
            "provider_write_executed": False,
            "messages_imported": 2,
        }
    )


@pytest.mark.asyncio
async def test_handle_message_dispatches_send_smtp():
    async def send_smtp_adapter(payload):
        assert payload["account"] == "mailbox-1"
        return {
            "status": "success",
            "message_id": "<sent-123@example.com>",
            "provider_write_executed": True,
        }

    connector = SelfHostedConnector(
        "ws://gateway.example/api/runner/ws",
        "token",
        smtp_send_handler=send_smtp_adapter,
    )
    original_handler = connector._handle_send_smtp
    connector._handle_send_smtp = AsyncMock(wraps=original_handler)
    connector.send_response = AsyncMock()

    await connector.handle_message(
        json.dumps(
            {
                "action": "send_smtp",
                "account": "mailbox-1",
                "request_id": "runner_req_2",
            }
        )
    )

    connector._handle_send_smtp.assert_awaited_once()
    connector.send_response.assert_awaited_once_with(
        {
            "status": "success",
            "action": "send_smtp",
            "protocol": "SMTP",
            "account": "mailbox-1",
            "request_id": "runner_req_2",
            "provider_write_executed": True,
            "message_id": "<sent-123@example.com>",
        }
    )


@pytest.mark.asyncio
async def test_handle_fetch_imap_fails_closed_without_adapter():
    connector = SelfHostedConnector("ws://gateway.example/api/runner/ws", "token")
    connector.send_response = AsyncMock()

    await connector.handle_message(
        json.dumps({"action": "fetch_imap", "account": "mailbox-1"})
    )

    connector.send_response.assert_awaited_once_with(
        {
            "status": "error",
            "action": "fetch_imap",
            "protocol": "IMAP",
            "account": "mailbox-1",
            "request_id": None,
            "provider_write_executed": False,
            "error": "adapter_not_configured",
        }
    )


@pytest.mark.asyncio
async def test_handle_send_smtp_fails_closed_without_adapter():
    connector = SelfHostedConnector("ws://gateway.example/api/runner/ws", "token")
    connector.send_response = AsyncMock()

    await connector.handle_message(
        json.dumps({"action": "send_smtp", "account": "mailbox-1"})
    )

    connector.send_response.assert_awaited_once_with(
        {
            "status": "error",
            "action": "send_smtp",
            "protocol": "SMTP",
            "account": "mailbox-1",
            "request_id": None,
            "provider_write_executed": False,
            "error": "adapter_not_configured",
        }
    )


@pytest.mark.asyncio
async def test_handle_message_dispatches_write_webdav():
    async def write_webdav_adapter(payload):
        assert payload["source_id"] == "webdav_src_1"
        return {
            "status": "success",
            "etag": "etag-after-write",
            "provider_write_executed": True,
        }

    connector = SelfHostedConnector(
        "ws://gateway.example/api/runner/ws",
        "token",
        webdav_write_handler=write_webdav_adapter,
    )
    connector.send_response = AsyncMock()

    await connector.handle_message(
        json.dumps(
            {
                "action": "write_webdav",
                "account": "webdav-primary",
                "source_id": "webdav_src_1",
                "request_id": "runner_req_webdav",
            }
        )
    )

    connector.send_response.assert_awaited_once_with(
        {
            "status": "success",
            "action": "write_webdav",
            "protocol": "WebDAV",
            "account": "webdav-primary",
            "request_id": "runner_req_webdav",
            "provider_write_executed": True,
            "etag": "etag-after-write",
        }
    )


@pytest.mark.asyncio
async def test_handle_write_webdav_fails_closed_without_adapter():
    connector = SelfHostedConnector("ws://gateway.example/api/runner/ws", "token")
    connector.send_response = AsyncMock()

    await connector.handle_message(
        json.dumps({"action": "write_webdav", "account": "webdav-primary"})
    )

    connector.send_response.assert_awaited_once_with(
        {
            "status": "error",
            "action": "write_webdav",
            "protocol": "WebDAV",
            "account": "webdav-primary",
            "request_id": None,
            "provider_write_executed": False,
            "error": "adapter_not_configured",
        }
    )


@pytest.mark.asyncio
async def test_handle_message_dispatches_write_caldav():
    async def write_caldav_adapter(payload):
        assert payload["source_id"] == "caldav_src_1"
        return {
            "status": "success",
            "etag": "etag-calendar-after-write",
            "provider_write_executed": True,
        }

    connector = SelfHostedConnector(
        "ws://gateway.example/api/runner/ws",
        "token",
        caldav_write_handler=write_caldav_adapter,
    )
    connector.send_response = AsyncMock()

    await connector.handle_message(
        json.dumps(
            {
                "action": "write_caldav",
                "account": "calendar-primary",
                "source_id": "caldav_src_1",
                "request_id": "runner_req_caldav",
            }
        )
    )

    connector.send_response.assert_awaited_once_with(
        {
            "status": "success",
            "action": "write_caldav",
            "protocol": "CalDAV",
            "account": "calendar-primary",
            "request_id": "runner_req_caldav",
            "provider_write_executed": True,
            "etag": "etag-calendar-after-write",
        }
    )


@pytest.mark.asyncio
async def test_handle_write_caldav_fails_closed_without_adapter():
    connector = SelfHostedConnector("ws://gateway.example/api/runner/ws", "token")
    connector.send_response = AsyncMock()

    await connector.handle_message(
        json.dumps({"action": "write_caldav", "account": "calendar-primary"})
    )

    connector.send_response.assert_awaited_once_with(
        {
            "status": "error",
            "action": "write_caldav",
            "protocol": "CalDAV",
            "account": "calendar-primary",
            "request_id": None,
            "provider_write_executed": False,
            "error": "adapter_not_configured",
        }
    )


@pytest.mark.asyncio
async def test_handle_message_reports_invalid_json():
    connector = SelfHostedConnector("ws://gateway.example/api/runner/ws", "token")
    connector.send_response = AsyncMock()

    await connector.handle_message("{not-json")

    connector.send_response.assert_awaited_once_with(
        {"status": "error", "action": None, "error": "invalid json"}
    )


@pytest.mark.asyncio
async def test_handle_message_reports_non_object_payload():
    connector = SelfHostedConnector("ws://gateway.example/api/runner/ws", "token")
    connector._handle_fetch_imap = AsyncMock()
    connector._handle_send_smtp = AsyncMock()
    connector.send_response = AsyncMock()

    await connector.handle_message(json.dumps(["fetch_imap"]))

    connector._handle_fetch_imap.assert_not_awaited()
    connector._handle_send_smtp.assert_not_awaited()
    connector.send_response.assert_awaited_once_with(
        {"status": "error", "action": None, "error": "invalid payload"}
    )


@pytest.mark.asyncio
async def test_handle_message_reports_unknown_action():
    connector = SelfHostedConnector("ws://gateway.example/api/runner/ws", "token")
    connector._handle_fetch_imap = AsyncMock()
    connector._handle_send_smtp = AsyncMock()
    connector.send_response = AsyncMock()

    await connector.handle_message(json.dumps({"action": "sync_unknown", "account": "mailbox-1"}))

    connector._handle_fetch_imap.assert_not_awaited()
    connector._handle_send_smtp.assert_not_awaited()
    connector.send_response.assert_awaited_once_with(
        {"status": "error", "action": "sync_unknown", "error": "unknown action"}
    )


@pytest.mark.asyncio
async def test_handle_fetch_imap_requires_account():
    connector = SelfHostedConnector("ws://gateway.example/api/runner/ws", "token")
    connector.send_response = AsyncMock()

    await connector.handle_message(json.dumps({"action": "fetch_imap"}))

    connector.send_response.assert_awaited_once_with(
        {"status": "error", "action": "fetch_imap", "error": "missing account"}
    )


@pytest.mark.asyncio
async def test_handle_fetch_imap_rejects_non_string_account():
    connector = SelfHostedConnector("ws://gateway.example/api/runner/ws", "token")
    connector.send_response = AsyncMock()

    await connector.handle_message(json.dumps({"action": "fetch_imap", "account": 7}))

    connector.send_response.assert_awaited_once_with(
        {"status": "error", "action": "fetch_imap", "error": "missing account"}
    )


@pytest.mark.asyncio
async def test_handle_send_smtp_requires_account():
    connector = SelfHostedConnector("ws://gateway.example/api/runner/ws", "token")
    connector.send_response = AsyncMock()

    await connector.handle_message(json.dumps({"action": "send_smtp"}))

    connector.send_response.assert_awaited_once_with(
        {"status": "error", "action": "send_smtp", "error": "missing account"}
    )


@pytest.mark.asyncio
async def test_handle_send_smtp_rejects_blank_account():
    connector = SelfHostedConnector("ws://gateway.example/api/runner/ws", "token")
    connector.send_response = AsyncMock()

    await connector.handle_message(json.dumps({"action": "send_smtp", "account": "  "}))

    connector.send_response.assert_awaited_once_with(
        {"status": "error", "action": "send_smtp", "error": "missing account"}
    )
