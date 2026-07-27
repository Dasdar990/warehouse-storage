"""SQLAlchemy ORM model for authenticated users (login + movement attribution)."""
import enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, Integer, String

from app.core.timezone import now_rome
from app.db import Base


class UserRole(str, enum.Enum):
    """Admins can manage users; operators can only use the warehouse tools."""

    ADMIN = "admin"
    OPERATOR = "operator"


class User(Base):
    """A person who can log in. `full_name` is what gets stamped on movements."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SAEnum(UserRole, native_enum=False, length=16), nullable=False, default=UserRole.OPERATOR)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=now_rome, nullable=False)
