import json
from unittest.mock import AsyncMock

import pytest

from runner.connector import SelfHostedConnector


@pytest.mark.asyncio
async def test_handle_message_dispatches_fetch_imap():
    connector = SelfHostedConnector("ws://gateway.example/api/runner/ws", "token")
    original_handler = connector._handle_fetch_imap
    connector._handle_fetch_imap = AsyncMock(wraps=original_handler)
    connector.send_response = AsyncMock()

    await connector.handle_message(json.dumps({"action": "fetch_imap", "account": "mailbox-1"}))

    connector._handle_fetch_imap.assert_awaited_once()
    connector.send_response.assert_awaited_once_with(
        {"status": "success", "action": "fetch_imap", "data": "IMAP data placeholder"}
    )


@pytest.mark.asyncio
async def test_handle_message_dispatches_send_smtp():
    connector = SelfHostedConnector("ws://gateway.example/api/runner/ws", "token")
    original_handler = connector._handle_send_smtp
    connector._handle_send_smtp = AsyncMock(wraps=original_handler)
    connector.send_response = AsyncMock()

    await connector.handle_message(json.dumps({"action": "send_smtp", "account": "mailbox-1"}))

    connector._handle_send_smtp.assert_awaited_once()
    connector.send_response.assert_awaited_once_with(
        {"status": "success", "action": "send_smtp", "message_id": "mock_id_123"}
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
