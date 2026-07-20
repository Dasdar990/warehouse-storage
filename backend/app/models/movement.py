"""SQLAlchemy ORM model for the live inventory movement / audit log."""
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base


class MovementAction(str, enum.Enum):
    """Whether stock was taken out or put back."""

    WITHDRAW = "withdraw"
    DEPOSIT = "deposit"


class MovementSource(str, enum.Enum):
    """How the operation was triggered -- drives the audit-log trust badge."""

    BARCODE = "barcode"
    MANUAL = "manual"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Movement(Base):
    """
    One row per stock movement (deposit or withdrawal).

    Denormalizes `pn` and `item_name` at write time so the audit log stays
    accurate and readable even if the parent item is later renamed or
    removed, while still keeping a live FK/relationship for convenience.
    """

    __tablename__ = "movements"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=_utcnow, nullable=False, index=True)

    item_id = Column(Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True, index=True)
    item_name = Column(String, nullable=False)
    pn = Column(String, nullable=False, index=True)
    shelf_position = Column(String, nullable=False)

    action = Column(SAEnum(MovementAction, native_enum=False, length=16), nullable=False)
    quantity = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)

    source = Column(SAEnum(MovementSource, native_enum=False, length=16), nullable=False)
    operator = Column(String, nullable=False, default="Operatore")

    item = relationship("Item")
