"""Background polling task.

Polls all active servers on a configurable interval using the A2S
(Steam Server Query) protocol. Reconciles joins and leaves against
open sessions in the database.

Since A2S only provides player names (not EOS IDs), players discovered
this way get a placeholder EOS ID in the format "a2s:{name}". These
will be replaced with real EOS IDs in Phase 2 when RCON or manual
linking is available.
"""

import asyncio
import logging

from sqlalchemy import select

from api.config import settings
from api.db import async_session_factory
from api.models.player import Player
from api.models.server import Server
from api.services.a2s_client import get_players
from api.services.player_resolver import (
    close_session,
    get_open_sessions_for_server,
    open_session,
    record_alias,
    upsert_player,
)

logger = logging.getLogger(__name__)


def _placeholder_eos_id(name: str) -> str:
    """Generate a placeholder EOS ID for A2S-discovered players."""
    safe = name.lower().replace(" ", "_")[:48]
    return f"a2s:{safe}"


class ServerPoller:
    def __init__(self) -> None:
        self._interval = settings.poll_interval_seconds

    async def run(self) -> None:
        logger.info("Server polling task started (interval=%ds)", self._interval)
        while True:
            try:
                await self._poll_all_servers()
            except Exception:
                logger.exception("Unexpected error during poll cycle")
            await asyncio.sleep(self._interval)

    async def _poll_all_servers(self) -> None:
        async with async_session_factory() as db:
            result = await db.execute(
                select(Server).where(
                    Server.active == True,  # noqa: E712
                    Server.query_host.isnot(None),
                    Server.query_port.isnot(None),
                )
            )
            servers = result.scalars().all()

        if not servers:
            logger.debug("No servers with query_host/query_port configured — skipping poll")
            return

        for server in servers:
            try:
                await self._poll_server(server)
            except Exception:
                logger.exception("Poll failed for server %s", server.name)

    async def _poll_server(self, server: Server) -> None:
        online = await get_players(server.query_host, server.query_port)
        online_by_eos = {_placeholder_eos_id(p.name): p for p in online}

        async with async_session_factory() as db:
            open_sessions = await get_open_sessions_for_server(db, server)

            # Players who joined (online but no open session)
            for eos_id, a2s_player in online_by_eos.items():
                if eos_id not in open_sessions:
                    player = await upsert_player(db, eos_id)
                    await record_alias(db, player, a2s_player.name)
                    await open_session(db, player, server, a2s_player.name)
                else:
                    # Still online — keep alias last_seen fresh
                    player_result = await db.execute(
                        select(Player).where(Player.eos_id == eos_id)
                    )
                    player = player_result.scalar_one_or_none()
                    if player:
                        await record_alias(db, player, a2s_player.name)

            # Players who left (open session but no longer online)
            for eos_id, session in open_sessions.items():
                if eos_id not in online_by_eos:
                    await close_session(db, session)

            await db.commit()

        logger.info(
            "Polled %s: %d online, %d previously tracked",
            server.name,
            len(online_by_eos),
            len(open_sessions),
        )
