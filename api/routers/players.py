from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.models.alias import Alias
from api.models.player import Player
from api.models.session import PlayerSession
from api.models.sighting import Sighting
from api.schemas.player import PlayerOut, PlayerSummary, PlayerUpsert
from api.schemas.session import SessionOut
from api.schemas.sighting import SightingOut

router = APIRouter()


@router.get("/{eos_id}", response_model=PlayerOut)
async def get_player(eos_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.eos_id == eos_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.post("/upsert", response_model=PlayerOut)
async def upsert_player(payload: PlayerUpsert, db: AsyncSession = Depends(get_db)):
    """Add a new player or update an existing one by EOS ID."""
    result = await db.execute(select(Player).where(Player.eos_id == payload.eos_id))
    player = result.scalar_one_or_none()
    now = datetime.now(UTC)

    if player is None:
        player = Player(eos_id=payload.eos_id)
        db.add(player)

    if payload.status is not None:
        player.status = payload.status
    if payload.tribe is not None:
        player.tribe = payload.tribe if payload.tribe != "" else None
    if payload.steam_id is not None:
        player.steam_id = payload.steam_id if payload.steam_id != "" else None
    if payload.notes is not None:
        player.notes = payload.notes if payload.notes != "" else None
    player.last_seen = now

    if payload.name:
        # Upsert alias
        alias_result = await db.execute(
            select(Alias).where(Alias.player_id == player.id, Alias.name == payload.name)
        ) if player.id else (None,)

        existing_alias = alias_result.scalar_one_or_none() if player.id else None
        if existing_alias:
            existing_alias.last_seen = now
        else:
            await db.flush()  # ensure player.id is set
            db.add(Alias(player_id=player.id, name=payload.name, first_seen=now, last_seen=now))

    await db.commit()
    await db.refresh(player)
    return player


@router.get("/{eos_id}/sessions", response_model=list[SessionOut])
async def get_player_sessions(eos_id: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
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


@router.get("/{eos_id}/sightings", response_model=list[SightingOut])
async def get_player_sightings(eos_id: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.eos_id == eos_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    sightings_result = await db.execute(
        select(Sighting)
        .where(Sighting.player_id == player.id)
        .order_by(Sighting.seen_at.desc())
        .limit(limit)
    )
    return sightings_result.scalars().all()


@router.get("/search/by-name", response_model=list[PlayerSummary])
async def search_by_name(q: str, db: AsyncSession = Depends(get_db)):
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
        player_result = await db.execute(select(Player).where(Player.id == alias.player_id))
        player = player_result.scalar_one_or_none()
        if player:
            players.append(player)

    return players


@router.get("/search/by-tribe", response_model=list[PlayerSummary])
async def search_by_tribe(q: str, db: AsyncSession = Depends(get_db)):
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    result = await db.execute(
        select(Player).where(Player.tribe.ilike(f"%{q}%")).limit(50)
    )
    return result.scalars().all()


@router.get("/search/by-status", response_model=list[PlayerSummary])
async def search_by_status(status: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Player).where(Player.status == status).order_by(Player.last_seen.desc()).limit(100)
    )
    return result.scalars().all()
