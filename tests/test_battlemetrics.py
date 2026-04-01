"""Unit tests for the BattleMetrics API client.

Uses respx to mock HTTP responses — no real network calls.
"""

import pytest
import httpx
import respx

from api.services.battlemetrics import BattleMetricsClient, BMPlayer


def _make_player_response(players: list[dict], included: list[dict] | None = None) -> dict:
    """Helper to build a minimal BattleMetrics JSON:API response."""
    return {
        "data": players,
        "included": included or [],
        "links": {},
    }


def _player_data(bm_id: str, name: str, identifier_ids: list[str]) -> dict:
    return {
        "type": "player",
        "id": bm_id,
        "attributes": {"name": name, "online": True},
        "relationships": {
            "identifiers": {"data": [{"type": "identifier", "id": iid} for iid in identifier_ids]}
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
    client = BattleMetricsClient(api_key="test-key")

    response_body = _make_player_response(
        players=[_player_data("bm1", "Raider123", ["ident1", "ident2"])],
        included=[
            _identifier("ident1", "eosID", "0002a1b2c3d4e5f6"),
            _identifier("ident2", "steamID", "76561198000000001"),
        ],
    )

    with respx.mock(base_url="https://api.battlemetrics.com") as mock:
        mock.get("/players").mock(return_value=httpx.Response(200, json=response_body))
        players = await client.get_online_players(bm_server_id)

    assert len(players) == 1
    p = players[0]
    assert p.name == "Raider123"
    assert p.eos_id == "0002a1b2c3d4e5f6"
    assert p.steam_id == "76561198000000001"
    assert p.bm_player_id == "bm1"

    await client.aclose()


@pytest.mark.asyncio
async def test_get_online_players_no_eos_id_fallback(bm_server_id):
    """Players without an eosID get a fallback bm: prefixed ID."""
    client = BattleMetricsClient(api_key="test-key")

    response_body = _make_player_response(
        players=[_player_data("bm99", "Anonymous", [])],
    )

    with respx.mock(base_url="https://api.battlemetrics.com") as mock:
        mock.get("/players").mock(return_value=httpx.Response(200, json=response_body))
        players = await client.get_online_players(bm_server_id)

    assert len(players) == 1
    assert players[0].eos_id == "bm:bm99"
    assert players[0].steam_id is None

    await client.aclose()


@pytest.mark.asyncio
async def test_get_online_players_multiple(bm_server_id):
    client = BattleMetricsClient(api_key="test-key")

    response_body = _make_player_response(
        players=[
            _player_data("bm1", "PlayerA", ["i1"]),
            _player_data("bm2", "123", ["i2"]),
            _player_data("bm3", "PlayerC", ["i3"]),
        ],
        included=[
            _identifier("i1", "eosID", "eos-aaa"),
            _identifier("i2", "eosID", "eos-bbb"),
            _identifier("i3", "eosID", "eos-ccc"),
        ],
    )

    with respx.mock(base_url="https://api.battlemetrics.com") as mock:
        mock.get("/players").mock(return_value=httpx.Response(200, json=response_body))
        players = await client.get_online_players(bm_server_id)

    assert len(players) == 3
    eos_ids = {p.eos_id for p in players}
    assert eos_ids == {"eos-aaa", "eos-bbb", "eos-ccc"}

    # Verify the anonymous "123" player is tracked by EOS ID
    anon = next(p for p in players if p.name == "123")
    assert anon.eos_id == "eos-bbb"

    await client.aclose()


@pytest.mark.asyncio
async def test_get_online_players_http_error(bm_server_id):
    """HTTP errors are caught and return an empty list."""
    client = BattleMetricsClient(api_key="test-key")

    with respx.mock(base_url="https://api.battlemetrics.com") as mock:
        mock.get("/players").mock(return_value=httpx.Response(429))
        players = await client.get_online_players(bm_server_id)

    assert players == []
    await client.aclose()


@pytest.mark.asyncio
async def test_get_online_players_empty_server(bm_server_id):
    client = BattleMetricsClient(api_key="test-key")

    response_body = _make_player_response(players=[])

    with respx.mock(base_url="https://api.battlemetrics.com") as mock:
        mock.get("/players").mock(return_value=httpx.Response(200, json=response_body))
        players = await client.get_online_players(bm_server_id)

    assert players == []
    await client.aclose()
