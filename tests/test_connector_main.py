from unittest.mock import AsyncMock, patch

import pytest

from connector import main as connector_main


class TestConnectorConfigError:
    def test_is_value_error_subclass(self):
        err = connector_main.ConnectorConfigError("bad config")
        assert isinstance(err, ValueError)


class TestBuildConnector:
    def test_requires_registration_token(self):
        with pytest.raises(connector_main.ConnectorConfigError, match="NARUON_REGISTRATION_TOKEN"):
            connector_main.build_connector({"NARUON_SESSION_TOKEN": "session"})

    def test_requires_session_token(self):
        with pytest.raises(connector_main.ConnectorConfigError, match="NARUON_SESSION_TOKEN"):
            connector_main.build_connector({"NARUON_REGISTRATION_TOKEN": "token"})

    def test_builds_with_default_ws_url(self):
        connector = connector_main.build_connector(
            {
                "NARUON_REGISTRATION_TOKEN": "reg token",
                "NARUON_SESSION_TOKEN": "sess",
            }
        )
        assert connector.target_ws_url == "wss://naruon.net/ws/runner/reg%20token"
        assert connector.token == "sess"

    def test_builds_with_custom_ws_url_template(self):
        connector = connector_main.build_connector(
            {
                "NARUON_CONTROL_PLANE_WS_URL": "wss://cp.example/ws/runner/{registration_token}",
                "NARUON_REGISTRATION_TOKEN": "r/t",
                "NARUON_SESSION_TOKEN": "sess",
            }
        )
        assert connector.target_ws_url == "wss://cp.example/ws/runner/r%2Ft"

    def test_builds_with_custom_ws_url_without_template(self):
        connector = connector_main.build_connector(
            {
                "NARUON_CONTROL_PLANE_WS_URL": "wss://cp.example/ws/runner",
                "NARUON_REGISTRATION_TOKEN": "token",
                "NARUON_SESSION_TOKEN": "sess",
            }
        )
        assert connector.target_ws_url == "wss://cp.example/ws/runner/token"


class TestAmain:
    @pytest.mark.asyncio
    async def test_connects_and_returns_zero(self):
        mock_connector = AsyncMock()
        with patch.object(connector_main, "build_connector", return_value=mock_connector):
            rc = await connector_main.amain(
                {
                    "NARUON_REGISTRATION_TOKEN": "token",
                    "NARUON_SESSION_TOKEN": "sess",
                }
            )
        assert rc == 0
        mock_connector.connect.assert_awaited_once()


class TestMain:
    def test_returns_zero_on_success(self, monkeypatch):
        async def fake_amain(environ=None):
            return 0

        monkeypatch.setattr(connector_main, "amain", fake_amain)
        assert connector_main.main() == 0

    def test_returns_2_on_config_error(self, monkeypatch):
        async def fake_amain(environ=None):
            raise connector_main.ConnectorConfigError("missing config")

        monkeypatch.setattr(connector_main, "amain", fake_amain)
        assert connector_main.main() == 2

    def test_returns_130_on_keyboard_interrupt(self, monkeypatch):
        async def fake_amain(environ=None):
            raise KeyboardInterrupt

        monkeypatch.setattr(connector_main, "amain", fake_amain)
        assert connector_main.main() == 130
