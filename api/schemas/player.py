import uuid
from datetime import datetime

from pydantic import BaseModel


class AliasOut(BaseModel):
    id: uuid.UUID
    name: str
    first_seen: datetime
    last_seen: datetime

    model_config = {"from_attributes": True}


class PlayerOut(BaseModel):
    id: uuid.UUID
    eos_id: str
    steam_id: str | None
    status: int
    tribe: str | None
    first_seen: datetime
    last_seen: datetime
    total_sessions: int
    notes: str | None
    aliases: list[AliasOut]

    model_config = {"from_attributes": True}


class PlayerSummary(BaseModel):
    id: uuid.UUID
    eos_id: str
    status: int
    tribe: str | None
    last_seen: datetime
    total_sessions: int

    model_config = {"from_attributes": True}


class PlayerUpsert(BaseModel):
    eos_id: str
    name: str | None = None
    status: int | None = None
    tribe: str | None = None
    steam_id: str | None = None
    notes: str | None = None
