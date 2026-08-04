"""SQLAlchemy ORM model for the live inventory movement / audit log."""
import enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.timezone import now_rome
from app.db import Base


class MovementAction(str, enum.Enum):
    """Whether stock was taken out, put back, or relocated to another shelf."""

    WITHDRAW = "withdraw"
    DEPOSIT = "deposit"
    MOVE = "move"
    EDIT = "edit"


class MovementSource(str, enum.Enum):
    """How the operation was triggered -- drives the audit-log trust badge."""

    BARCODE = "barcode"
    MANUAL = "manual"


class Movement(Base):
    """
    One row per stock movement (deposit or withdrawal).

    Denormalizes `pn` and `item_name` at write time so the audit log stays
    accurate and readable even if the parent item is later renamed or
    removed, while still keeping a live FK/relationship for convenience.
    """

    __tablename__ = "movements"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True),
                       default=now_rome, nullable=False, index=True)

    item_id = Column(Integer, ForeignKey(
        "items.id", ondelete="SET NULL"), nullable=True, index=True)
    item_name = Column(String, nullable=False)
    pn = Column(String, nullable=False, index=True)
    shelf_position = Column(String, nullable=False)
    # Only set on MOVE rows: the shelf the item was on *before* the move.
    # `shelf_position` above holds the destination shelf, consistent with
    # how it always reflects the item's shelf at the time of the entry.
    from_shelf_position = Column(String, nullable=True)
    # Only set on *partial* MOVE rows (see move_item): `item_id` above is the
    # destination item that received the moved quantity, while this points
    # back at the source item it was split off from -- both are needed to
    # roll a split move back correctly (it touches two different items'
    # quantities, unlike a full move which just relocates one row).
    split_from_item_id = Column(Integer, ForeignKey(
        "items.id", ondelete="SET NULL"), nullable=True)

    action = Column(SAEnum(MovementAction, native_enum=False,
                    length=16), nullable=False)
    quantity = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)

    source = Column(SAEnum(MovementSource, native_enum=False,
                    length=16), nullable=False)
    operator = Column(String, nullable=False, default="Operator")

    # Rollback support (admin-only). The audit log stays append-only: a
    # rollback never edits or deletes the original row, it just flags it
    # and writes a new, opposite compensating movement pointing back here.
    voided = Column(Boolean, nullable=False, default=False)
    reversal_of_id = Column(Integer, ForeignKey("movements.id"), nullable=True)

    # Explicit `foreign_keys` needed: with `split_from_item_id` added above,
    # there are now two FK columns pointing at items.id, so SQLAlchemy can no
    # longer infer on its own which one this relationship should join on.
    item = relationship("Item", foreign_keys=[item_id])
