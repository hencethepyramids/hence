"""Background polling task.

Runs on a configurable interval, fetches current players from BattleMetrics
for every active official server, and reconciles joins/leaves against the DB.
"""

import asyncio
import logging

from sqlalchemy import select

from api.config import settings
from api.db import async_session_factory
from api.models.player import Player
from api.models.server import Server, ServerType
from api.services.battlemetrics import BattleMetricsClient
from api.services.player_resolver import (
    close_session,
    get_open_sessions_for_server,
    open_session,
    record_alias,
    upsert_player,
)

logger = logging.getLogger(__name__)


class BattleMetricsPoller:
    def __init__(self) -> None:
        self._interval = settings.poll_interval_seconds
        self._client: BattleMetricsClient | None = None

    async def run(self) -> None:
        if not settings.battlemetrics_api_key:
            logger.warning("BATTLEMETRICS_API_KEY not set — polling disabled")
            return

        self._client = BattleMetricsClient()
        try:
            while True:
                try:
                    await self._poll_all_servers()
                except Exception:
                    logger.exception("Unexpected error during poll cycle")
                await asyncio.sleep(self._interval)
        finally:
            await self._client.aclose()

    async def _poll_all_servers(self) -> None:
        async with async_session_factory() as db:
            result = await db.execute(
                select(Server).where(
                    Server.active == True,  # noqa: E712
                    Server.type == ServerType.official,
                    Server.battlemetrics_id.isnot(None),
                )
            )
            servers = result.scalars().all()

        for server in servers:
            try:
                await self._poll_server(server)
            except Exception:
                logger.exception("Poll failed for server %s (%s)", server.name, server.battlemetrics_id)

    async def _poll_server(self, server: Server) -> None:
        online = await self._client.get_online_players(server.battlemetrics_id)
        online_by_eos = {p.eos_id: p for p in online}

        async with async_session_factory() as db:
            open_sessions = await get_open_sessions_for_server(db, server)

            # Players who joined (online but no open session)
            for eos_id, bm_player in online_by_eos.items():
                if eos_id not in open_sessions:
                    player = await upsert_player(db, eos_id, bm_player.steam_id)
                    await record_alias(db, player, bm_player.name)
                    await open_session(db, player, server, bm_player.name)
                else:
                    # Still online — update alias last_seen
                    player_result = await db.execute(
                        select(Player).where(Player.eos_id == eos_id)
                    )
                    player = player_result.scalar_one_or_none()
                    if player:
                        await record_alias(db, player, bm_player.name)

            # Players who left (open session but no longer online)
            for eos_id, session in open_sessions.items():
                if eos_id not in online_by_eos:
                    await close_session(db, session)

            await db.commit()

        logger.debug(
            "Polled %s: %d online, %d previously open sessions",
            server.name,
            len(online_by_eos),
            len(open_sessions),
        )
