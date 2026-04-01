from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.models.alias import Alias
from api.models.player import Player
from api.models.session import PlayerSession
from api.schemas.player import PlayerOut, PlayerSummary
from api.schemas.session import SessionOut

router = APIRouter()


@router.get("/{eos_id}", response_model=PlayerOut)
async def get_player(eos_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.eos_id == eos_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.get("/{eos_id}/sessions", response_model=list[SessionOut])
async def get_player_sessions(
    eos_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Player).where(Player.eos_id == eos_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    sessions_result = await db.execute(
        select(PlayerSession)
        .where(PlayerSession.player_id == player.id)
        .order_by(PlayerSession.joined_at.desc())
        .limit(limit)
    )
    return sessions_result.scalars().all()


@router.get("/search/by-name", response_model=list[PlayerSummary])
async def search_by_name(q: str, db: AsyncSession = Depends(get_db)):
    """Search players by partial name match across all known aliases."""
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    alias_result = await db.execute(
        select(Alias).where(Alias.name.ilike(f"%{q}%")).limit(50)
    )
    aliases = alias_result.scalars().all()

    seen_player_ids = set()
    players = []
    for alias in aliases:
        if alias.player_id in seen_player_ids:
            continue
        seen_player_ids.add(alias.player_id)
        player_result = await db.execute(
            select(Player).where(Player.id == alias.player_id)
        )
        player = player_result.scalar_one_or_none()
        if player:
            players.append(player)

    return players
