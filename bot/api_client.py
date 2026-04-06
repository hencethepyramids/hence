"""HTTP client for the Hence FastAPI backend.

All Discord commands go through this client rather than touching the DB
directly, keeping the bot stateless and the API as the single source of truth.
"""

import logging

import httpx

from bot.config import settings

logger = logging.getLogger(__name__)


class HenceAPI:
    def __init__(self, base_url: str | None = None) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url or settings.api_base_url,
            timeout=10.0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_player(self, eos_id: str) -> dict | None:
        try:
            resp = await self._client.get(f"/players/{eos_id}")
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("get_player failed: %s", exc)
            return None

    async def upsert_player(
        self,
        eos_id: str,
        name: str | None = None,
        status: int | None = None,
        tribe: str | None = None,
        steam_id: str | None = None,
        notes: str | None = None,
    ) -> dict | None:
        payload: dict = {"eos_id": eos_id}
        if name is not None:
            payload["name"] = name
        if status is not None:
            payload["status"] = status
        if tribe is not None:
            payload["tribe"] = tribe
        if steam_id is not None:
            payload["steam_id"] = steam_id
        if notes is not None:
            payload["notes"] = notes
        try:
            resp = await self._client.post("/players/upsert", json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("upsert_player failed: %s", exc)
            return None

    async def report_sighting(
        self,
        eos_id: str,
        server_name: str,
        reported_by_discord_id: str,
        reported_by_name: str,
    ) -> dict | None:
        try:
            resp = await self._client.post(
                "/sightings/",
                json={
                    "eos_id": eos_id,
                    "server_name": server_name,
                    "reported_by_discord_id": reported_by_discord_id,
                    "reported_by_name": reported_by_name,
                },
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("report_sighting failed: %s", exc)
            return None

    async def get_player_sightings(self, eos_id: str, limit: int = 10) -> list[dict]:
        try:
            resp = await self._client.get(f"/players/{eos_id}/sightings", params={"limit": limit})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("get_player_sightings failed: %s", exc)
            return []

    async def get_player_sessions(self, eos_id: str, limit: int = 10) -> list[dict]:
        try:
            resp = await self._client.get(f"/players/{eos_id}/sessions", params={"limit": limit})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("get_player_sessions failed: %s", exc)
            return []

    async def search_players(self, name: str) -> list[dict]:
        try:
            resp = await self._client.get("/players/search/by-name", params={"q": name})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("search_players failed: %s", exc)
            return []

    async def search_by_tribe(self, tribe: str) -> list[dict]:
        try:
            resp = await self._client.get("/players/search/by-tribe", params={"q": tribe})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("search_by_tribe failed: %s", exc)
            return []

    async def search_by_status(self, status: int) -> list[dict]:
        try:
            resp = await self._client.get("/players/search/by-status", params={"status": status})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("search_by_status failed: %s", exc)
            return []

    async def get_servers(self) -> list[dict]:
        try:
            resp = await self._client.get("/servers/")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("get_servers failed: %s", exc)
            return []

    async def add_server(self, name: str, server_type: str, battlemetrics_id: str) -> dict | None:
        try:
            resp = await self._client.post(
                "/servers/",
                json={"name": name, "type": server_type, "battlemetrics_id": battlemetrics_id},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("add_server failed: %s", exc)
            return None

    async def remove_server(self, server_id: str) -> bool:
        try:
            resp = await self._client.delete(f"/servers/{server_id}")
            return resp.status_code == 204
        except httpx.HTTPError as exc:
            logger.error("remove_server failed: %s", exc)
            return False
