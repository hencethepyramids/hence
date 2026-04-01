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

    async def get_player_sessions(self, eos_id: str, limit: int = 10) -> list[dict]:
        try:
            resp = await self._client.get(f"/players/{eos_id}/sessions", params={"limit": limit})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("get_player_sessions failed: %s", exc)
            return []

    async def get_online_players(self) -> list[dict]:
        try:
            resp = await self._client.get("/sessions/online")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("get_online_players failed: %s", exc)
            return []

    async def search_players(self, name: str) -> list[dict]:
        try:
            resp = await self._client.get("/players/search/by-name", params={"q": name})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("search_players failed: %s", exc)
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
