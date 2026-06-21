# Naruon Self-hosted Connector

The connector opens an outbound WebSocket to the Naruon control plane and
executes only configured local adapters. Without adapters, runner commands fail
closed with `adapter_not_configured` and `provider_write_executed=false`.

## Required Environment

- `NARUON_REGISTRATION_TOKEN`: server-issued runner registration token used in
  the WebSocket path.
- `NARUON_SESSION_TOKEN`: signed Naruon session token sent as the WebSocket
  bearer credential.

Optional:

- `NARUON_CONTROL_PLANE_WS_URL`: defaults to
  `wss://naruon.net/ws/runner/{registration_token}`.
- `NARUON_CONNECTOR_LOG_LEVEL`: defaults to `INFO`.

## Run

```bash
docker build -f connector/Dockerfile -t naruon-connector .
docker run --rm \
  -e NARUON_REGISTRATION_TOKEN=... \
  -e NARUON_SESSION_TOKEN=... \
  naruon-connector
```
