from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.models.player import Player
from api.models.sighting import Sighting
from api.schemas.sighting import SightingCreate, SightingOut

router = APIRouter()


@router.post("/", response_model=SightingOut, status_code=201)
async def report_sighting(payload: SightingCreate, db: AsyncSession = Depends(get_db)):
    """Record a manually reported player sighting on a server."""
    result = await db.execute(select(Player).where(Player.eos_id == payload.eos_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found — add them first with POST /players/upsert")

    sighting = Sighting(
        player_id=player.id,
        server_name=payload.server_name,
        seen_at=datetime.now(UTC),
        reported_by_discord_id=payload.reported_by_discord_id,
        reported_by_name=payload.reported_by_name,
    )
    db.add(sighting)
    player.last_seen = sighting.seen_at
    await db.commit()
    await db.refresh(sighting)
    return sighting
