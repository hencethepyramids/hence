"""BattleMetrics API client.

BattleMetrics uses JSON:API format. For ARK:SA servers, player identifiers
include type "eosID" (Epic Online Services) and "steamID". We prioritise
eosID as the canonical player identifier.

If a player has no eosID on BattleMetrics, we fall back to their BattleMetrics
player ID prefixed with "bm:" so it remains distinct from real EOS IDs.
"""

import logging
from dataclasses import dataclass

import httpx

from api.config import settings

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.battlemetrics.com"
# Identifier types BattleMetrics uses for ARK:SA EOS IDs
_EOS_IDENTIFIER_TYPES = {"eosID", "eosId", "eos"}


@dataclass
class BMPlayer:
    """Parsed player data from a single BattleMetrics poll."""

    bm_player_id: str
    name: str
    eos_id: str          # EOS ID if found, else "bm:{bm_player_id}"
    steam_id: str | None


class BattleMetricsClient:
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.battlemetrics_api_key
        headers = {"Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers=headers,
            timeout=15.0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_online_players(self, battlemetrics_server_id: str) -> list[BMPlayer]:
        """Return players currently online on the given BM server."""
        players: list[BMPlayer] = []
        url = "/players"
        params = {
            "filter[servers]": battlemetrics_server_id,
            "filter[online]": "true",
            "include": "identifier",
            "page[size]": 100,
        }

        while url:
            try:
                resp = await self._client.get(url, params=params)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                logger.error("BattleMetrics request failed: %s", exc)
                break

            body = resp.json()
            included = {
                item["id"]: item
                for item in body.get("included", [])
                if item.get("type") == "identifier"
            }

            for player_data in body.get("data", []):
                bm_id = player_data["id"]
                name = player_data["attributes"].get("name", "Unknown")
                identifier_refs = (
                    player_data.get("relationships", {})
                    .get("identifiers", {})
                    .get("data", [])
                )

                eos_id: str | None = None
                steam_id: str | None = None

                for ref in identifier_refs:
                    ident = included.get(ref["id"])
                    if not ident:
                        continue
                    ident_type = ident["attributes"].get("type", "")
                    ident_value = ident["attributes"].get("identifier", "")
                    if ident_type in _EOS_IDENTIFIER_TYPES:
                        eos_id = ident_value
                    elif ident_type in {"steamID", "steamId", "steam"}:
                        steam_id = ident_value

                players.append(
                    BMPlayer(
                        bm_player_id=bm_id,
                        name=name,
                        eos_id=eos_id or f"bm:{bm_id}",
                        steam_id=steam_id,
                    )
                )

            # Pagination — BattleMetrics uses cursor-based links
            next_link = body.get("links", {}).get("next")
            if next_link:
                url = next_link
                params = {}  # next link already contains all query params
            else:
                url = None

        return players

    async def get_server_info(self, battlemetrics_server_id: str) -> dict | None:
        """Return server info including IP and query port from BattleMetrics.

        Returns a dict with keys: name, ip, port, portQuery (Steam A2S query port).
        """
        try:
            resp = await self._client.get(f"/servers/{battlemetrics_server_id}")
            resp.raise_for_status()
            attrs = resp.json().get("data", {}).get("attributes", {})
            return {
                "name": attrs.get("name"),
                "ip": attrs.get("ip"),
                "port": attrs.get("port"),
                "portQuery": attrs.get("portQuery"),
            }
        except httpx.HTTPError as exc:
            logger.error("Failed to fetch server info for %s: %s", battlemetrics_server_id, exc)
            return None
