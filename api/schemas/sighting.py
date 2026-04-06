import uuid
from datetime import datetime

from pydantic import BaseModel


class SightingOut(BaseModel):
    id: uuid.UUID
    player_id: uuid.UUID
    server_name: str
    seen_at: datetime
    reported_by_discord_id: str
    reported_by_name: str

    model_config = {"from_attributes": True}


class SightingCreate(BaseModel):
    eos_id: str
    server_name: str
    reported_by_discord_id: str
    reported_by_name: str
