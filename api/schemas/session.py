import uuid
from datetime import datetime

from pydantic import BaseModel


class SessionOut(BaseModel):
    id: uuid.UUID
    player_id: uuid.UUID
    server_id: uuid.UUID
    joined_at: datetime
    left_at: datetime | None
    duration_minutes: int | None
    name_used: str

    model_config = {"from_attributes": True}


class OnlinePlayer(BaseModel):
    eos_id: str
    current_name: str
    server_name: str
    server_id: uuid.UUID
    joined_at: datetime
