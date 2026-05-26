import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_caldav_event_parsing_and_sync():
    from services.caldav_service import sync_caldav_accounts

    session_mock = AsyncMock()
    # Mock finding accounts
    account_mock = MagicMock()
    account_mock.server_url = "https://caldav.example.com"
    account_mock.username = "user"
    account_mock.credentials_encrypted = "pass"

    execute_res = MagicMock()
    execute_res.scalars.return_value.all.return_value = [account_mock]
    session_mock.execute.return_value = execute_res

    with patch("services.caldav_service.logger") as logger_mock:
        await sync_caldav_accounts(session_mock, "user_1")
        # Should have logged parsing
        assert logger_mock.info.called


@pytest.mark.asyncio
async def test_webdav_file_listing_and_sync():
    from services.webdav_service import sync_webdav_folders

    session_mock = AsyncMock()
    account_mock = MagicMock()
    account_mock.server_url = "https://webdav.example.com"

    execute_res = MagicMock()
    execute_res.scalars.return_value.all.return_value = [account_mock]
    session_mock.execute.return_value = execute_res

    with patch("services.webdav_service.logger") as logger_mock:
        await sync_webdav_folders(session_mock, "user_1")
        assert logger_mock.info.called
