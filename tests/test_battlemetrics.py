"""Unit tests for the BattleMetrics API client.

Uses a custom httpx AsyncBaseTransport for mocking — avoids respx/httpx
version compatibility issues entirely.
"""

import httpx
import pytest

from api.services.battlemetrics import BattleMetricsClient

_BASE_URL = "https://api.battlemetrics.com"


class _MockTransport(httpx.AsyncBaseTransport):
    """Minimal httpx transport that returns a fixed response for any request."""

    def __init__(self, response: httpx.Response) -> None:
        self._response = response

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return self._response


def _client_with(response: httpx.Response) -> BattleMetricsClient:
    http = httpx.AsyncClient(
        base_url=_BASE_URL,
        transport=_MockTransport(response),
    )
    return BattleMetricsClient(client=http)


def _json_response(data: dict) -> httpx.Response:
    return httpx.Response(200, json=data)


def _make_body(players: list[dict], included: list[dict] | None = None) -> dict:
    return {"data": players, "included": included or [], "links": {}}


def _player(bm_id: str, name: str, identifier_ids: list[str]) -> dict:
    return {
        "type": "player",
        "id": bm_id,
        "attributes": {"name": name, "online": True},
        "relationships": {
            "identifiers": {"data": [{"type": "identifier", "id": i} for i in identifier_ids]}
        },
    }


def _identifier(iid: str, ident_type: str, value: str) -> dict:
    return {
        "type": "identifier",
        "id": iid,
        "attributes": {"type": ident_type, "identifier": value},
    }


@pytest.mark.asyncio
async def test_get_online_players_with_eos_id(bm_server_id):
    body = _make_body(
        players=[_player("bm1", "Raider123", ["ident1", "ident2"])],
        included=[
            _identifier("ident1", "eosID", "0002a1b2c3d4e5f6"),
            _identifier("ident2", "steamID", "76561198000000001"),
        ],
    )
    client = _client_with(_json_response(body))
    players = await client.get_online_players(bm_server_id)
    await client.aclose()

    assert len(players) == 1
    p = players[0]
    assert p.name == "Raider123"
    assert p.eos_id == "0002a1b2c3d4e5f6"
    assert p.steam_id == "76561198000000001"
    assert p.bm_player_id == "bm1"


@pytest.mark.asyncio
async def test_get_online_players_no_eos_id_fallback(bm_server_id):
    """Players without an eosID get a fallback bm: prefixed ID."""
    body = _make_body(players=[_player("bm99", "Anonymous", [])])
    client = _client_with(_json_response(body))
    players = await client.get_online_players(bm_server_id)
    await client.aclose()

    assert len(players) == 1
    assert players[0].eos_id == "bm:bm99"
    assert players[0].steam_id is None


@pytest.mark.asyncio
async def test_get_online_players_multiple(bm_server_id):
    body = _make_body(
        players=[
            _player("bm1", "PlayerA", ["i1"]),
            _player("bm2", "123", ["i2"]),
            _player("bm3", "PlayerC", ["i3"]),
        ],
        included=[
            _identifier("i1", "eosID", "eos-aaa"),
            _identifier("i2", "eosID", "eos-bbb"),
            _identifier("i3", "eosID", "eos-ccc"),
        ],
    )
    client = _client_with(_json_response(body))
    players = await client.get_online_players(bm_server_id)
    await client.aclose()

    assert len(players) == 3
    assert {p.eos_id for p in players} == {"eos-aaa", "eos-bbb", "eos-ccc"}
    anon = next(p for p in players if p.name == "123")
    assert anon.eos_id == "eos-bbb"


@pytest.mark.asyncio
async def test_get_online_players_http_error(bm_server_id):
    """HTTP errors are caught and return an empty list."""
    client = _client_with(httpx.Response(429))
    players = await client.get_online_players(bm_server_id)
    await client.aclose()

    assert players == []


@pytest.mark.asyncio
async def test_get_online_players_empty_server(bm_server_id):
    body = _make_body(players=[])
    client = _client_with(_json_response(body))
    players = await client.get_online_players(bm_server_id)
    await client.aclose()

    assert players == []
