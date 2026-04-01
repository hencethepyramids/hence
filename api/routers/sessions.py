from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.models.player import Player
from api.models.server import Server
from api.models.session import PlayerSession
from api.schemas.session import OnlinePlayer

router = APIRouter()


@router.get("/online", response_model=list[OnlinePlayer])
async def get_online_players(db: AsyncSession = Depends(get_db)):
    """Return all players with an open (non-closed) session."""
    result = await db.execute(
        select(PlayerSession, Player.eos_id, Server.name.label("server_name"))
        .join(Player, PlayerSession.player_id == Player.id)
        .join(Server, PlayerSession.server_id == Server.id)
        .where(PlayerSession.left_at.is_(None))
        .order_by(PlayerSession.joined_at.desc())
    )

    rows = result.all()
    return [
        OnlinePlayer(
            eos_id=eos_id,
            current_name=sess.name_used,
            server_name=server_name,
            server_id=sess.server_id,
            joined_at=sess.joined_at,
        )
        for sess, eos_id, server_name in rows
    ]
