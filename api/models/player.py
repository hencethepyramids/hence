import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from api.models.base import Base

if TYPE_CHECKING:
    from api.models.alias import Alias
    from api.models.session import PlayerSession


class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    eos_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    steam_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    aliases: Mapped[list["Alias"]] = relationship("Alias", back_populates="player", lazy="selectin")
    sessions: Mapped[list["PlayerSession"]] = relationship("PlayerSession", back_populates="player", lazy="select")
