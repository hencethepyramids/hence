import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base

if TYPE_CHECKING:
    from api.models.session import PlayerSession


class ServerType(str, enum.Enum):
    official = "official"
    private = "private"


class Server(Base):
    __tablename__ = "servers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    type: Mapped[ServerType] = mapped_column(Enum(ServerType, name="servertype"), nullable=False)
    battlemetrics_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    query_host: Mapped[str | None] = mapped_column(String(256), nullable=True)
    query_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rcon_host: Mapped[str | None] = mapped_column(String(256), nullable=True)
    rcon_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    sessions: Mapped[list["PlayerSession"]] = relationship("PlayerSession", back_populates="server", lazy="select")
