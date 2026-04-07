import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from api.models.base import Base

if TYPE_CHECKING:
    from api.models.player import Player


class Sighting(Base):
    """A manually reported observation of a player on a server.

    Unlike sessions (which require polling), sightings are submitted by
    community members who see a player in-game on an official server.
    """

    __tablename__ = "sightings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    server_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reported_by_discord_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reported_by_name: Mapped[str] = mapped_column(String(128), nullable=False)

    player: Mapped["Player"] = relationship("Player", back_populates="sightings")
