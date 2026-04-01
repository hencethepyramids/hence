"""Player resolution — upsert players, aliases, and sessions.

All writes go through these helpers so the rest of the codebase never
touches the ORM directly for player identity operations.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.alias import Alias
from api.models.player import Player
from api.models.server import Server
from api.models.session import PlayerSession

logger = logging.getLogger(__name__)


async def upsert_player(db: AsyncSession, eos_id: str, steam_id: str | None = None) -> Player:
    """Return the Player for this EOS ID, creating it if it doesn't exist."""
    result = await db.execute(select(Player).where(Player.eos_id == eos_id))
    player = result.scalar_one_or_none()

    if player is None:
        player = Player(eos_id=eos_id, steam_id=steam_id)
        db.add(player)
        await db.flush()
        logger.info("New player registered: eos_id=%s", eos_id)
    else:
        player.last_seen = datetime.now(UTC)
        if steam_id and not player.steam_id:
            player.steam_id = steam_id

    return player


async def record_alias(db: AsyncSession, player: Player, name: str) -> None:
    """Ensure this display name is recorded for the player."""
    result = await db.execute(
        select(Alias).where(Alias.player_id == player.id, Alias.name == name)
    )
    alias = result.scalar_one_or_none()
    now = datetime.now(UTC)

    if alias is None:
        alias = Alias(player_id=player.id, name=name, first_seen=now, last_seen=now)
        db.add(alias)
        logger.debug("New alias recorded: player=%s name=%r", player.eos_id, name)
    else:
        alias.last_seen = now


async def open_session(db: AsyncSession, player: Player, server: Server, name: str) -> PlayerSession:
    """Open a new session for a player who just joined."""
    session = PlayerSession(
        player_id=player.id,
        server_id=server.id,
        joined_at=datetime.now(UTC),
        name_used=name,
    )
    db.add(session)
    player.total_sessions += 1
    await db.flush()
    logger.info("Session opened: eos_id=%s server=%s", player.eos_id, server.name)
    return session


async def close_session(db: AsyncSession, session: PlayerSession) -> None:
    """Close an open session and compute its duration."""
    now = datetime.now(UTC)
    session.left_at = now
    delta = now - session.joined_at.replace(tzinfo=UTC) if session.joined_at.tzinfo is None else now - session.joined_at
    session.duration_minutes = max(0, int(delta.total_seconds() / 60))
    logger.info(
        "Session closed: player_id=%s server_id=%s duration=%dm",
        session.player_id,
        session.server_id,
        session.duration_minutes,
    )


async def get_open_sessions_for_server(db: AsyncSession, server: Server) -> dict[str, PlayerSession]:
    """Return {eos_id: PlayerSession} for all open sessions on this server."""
    result = await db.execute(
        select(PlayerSession, Player.eos_id)
        .join(Player, PlayerSession.player_id == Player.id)
        .where(
            PlayerSession.server_id == server.id,
            PlayerSession.left_at.is_(None),
        )
    )
    return {eos_id: sess for sess, eos_id in result.all()}
