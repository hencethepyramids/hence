"""Unit tests for the BattleMetrics API client.

Uses respx to mock HTTP responses — no real network calls.
"""

import httpx
import pytest
import respx

from api.services.battlemetrics import BattleMetricsClient, BMPlayer

_BM_PLAYERS_URL = "https://api.battlemetrics.com/players"


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
    response_body = _make_player_response(
        players=[_player_data("bm1", "Raider123", ["ident1", "ident2"])],
        included=[
            _identifier("ident1", "eosID", "0002a1b2c3d4e5f6"),
            _identifier("ident2", "steamID", "76561198000000001"),
        ],
    )

    with respx.mock() as mock:
        mock.get(_BM_PLAYERS_URL).mock(return_value=httpx.Response(200, json=response_body))
        client = BattleMetricsClient(api_key="test-key")
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
    response_body = _make_player_response(
        players=[_player_data("bm99", "Anonymous", [])],
    )

    with respx.mock() as mock:
        mock.get(_BM_PLAYERS_URL).mock(return_value=httpx.Response(200, json=response_body))
        client = BattleMetricsClient(api_key="test-key")
        players = await client.get_online_players(bm_server_id)
        await client.aclose()

    assert len(players) == 1
    assert players[0].eos_id == "bm:bm99"
    assert players[0].steam_id is None


@pytest.mark.asyncio
async def test_get_online_players_multiple(bm_server_id):
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

    with respx.mock() as mock:
        mock.get(_BM_PLAYERS_URL).mock(return_value=httpx.Response(200, json=response_body))
        client = BattleMetricsClient(api_key="test-key")
        players = await client.get_online_players(bm_server_id)
        await client.aclose()

    assert len(players) == 3
    eos_ids = {p.eos_id for p in players}
    assert eos_ids == {"eos-aaa", "eos-bbb", "eos-ccc"}

    # Verify the anonymous "123" player is tracked by EOS ID
    anon = next(p for p in players if p.name == "123")
    assert anon.eos_id == "eos-bbb"


@pytest.mark.asyncio
async def test_get_online_players_http_error(bm_server_id):
    """HTTP errors are caught and return an empty list."""
    with respx.mock() as mock:
        mock.get(_BM_PLAYERS_URL).mock(return_value=httpx.Response(429))
        client = BattleMetricsClient(api_key="test-key")
        players = await client.get_online_players(bm_server_id)
        await client.aclose()

    assert players == []


@pytest.mark.asyncio
async def test_get_online_players_empty_server(bm_server_id):
    response_body = _make_player_response(players=[])

    with respx.mock() as mock:
        mock.get(_BM_PLAYERS_URL).mock(return_value=httpx.Response(200, json=response_body))
        client = BattleMetricsClient(api_key="test-key")
        players = await client.get_online_players(bm_server_id)
        await client.aclose()

    assert players == []
