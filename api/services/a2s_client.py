"""Steam A2S (Server Query) client.

Uses the A2S protocol to query ARK game servers directly for their live
player list. Returns player names and session durations.

A2S is the only reliable way to get player lists from official ARK:SA
servers — BattleMetrics does not expose player lists for this game.
"""

import asyncio
import logging
from dataclasses import dataclass

import a2s

logger = logging.getLogger(__name__)

_TIMEOUT = 5.0


@dataclass
class A2SPlayer:
    name: str
    duration_seconds: float


async def get_players(host: str, port: int) -> list[A2SPlayer]:
    """Return the current player list from a game server via A2S.

    Returns an empty list if the server is unreachable or times out.
    """
    address = (host, port)
    try:
        players = await asyncio.to_thread(a2s.players, address, timeout=_TIMEOUT)
        return [
            A2SPlayer(name=p.name, duration_seconds=p.duration)
            for p in players
            if p.name  # filter out empty names (bots/slots)
        ]
    except Exception as exc:
        logger.warning("A2S query failed for %s:%d — %s", host, port, exc)
        return []
