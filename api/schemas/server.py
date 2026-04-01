import uuid

from pydantic import BaseModel

from api.models.server import ServerType


class ServerOut(BaseModel):
    id: uuid.UUID
    name: str
    type: ServerType
    battlemetrics_id: str | None
    rcon_host: str | None
    rcon_port: int | None
    active: bool

    model_config = {"from_attributes": True}


class ServerCreate(BaseModel):
    name: str
    type: ServerType
    battlemetrics_id: str | None = None
    rcon_host: str | None = None
    rcon_port: int | None = None
