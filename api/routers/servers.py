import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.models.server import Server
from api.schemas.server import ServerCreate, ServerOut

router = APIRouter()


@router.get("/", response_model=list[ServerOut])
async def list_servers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Server).order_by(Server.name))
    return result.scalars().all()


@router.post("/", response_model=ServerOut, status_code=201)
async def add_server(payload: ServerCreate, db: AsyncSession = Depends(get_db)):
    server = Server(**payload.model_dump())
    db.add(server)
    await db.commit()
    await db.refresh(server)
    return server


@router.delete("/{server_id}", status_code=204)
async def remove_server(server_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    await db.delete(server)
    await db.commit()


@router.patch("/{server_id}/active", response_model=ServerOut)
async def set_server_active(server_id: uuid.UUID, active: bool, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    server.active = active
    await db.commit()
    await db.refresh(server)
    return server
