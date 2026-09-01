"""User CRUD and authentication lookups."""
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, UserUpdate

settings = get_settings()


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.execute(select(User).where(User.username == username)).scalar_one_or_none()


def normalize_badge_uid(raw: str) -> str:
    """
    Same normalization the badge reader applies (uppercase, no separators),
    so a badge scanned by the bridge always matches what's stored here
    regardless of how an admin happened to type/paste it in.
    """
    cleaned = raw.strip().upper()
    for sep in (":", "-", " "):
        cleaned = cleaned.replace(sep, "")
    return cleaned


def get_user_by_badge_uid(db: Session, badge_uid: str) -> User | None:
    normalized = normalize_badge_uid(badge_uid)
    if not normalized:
        return None
    return db.execute(select(User).where(User.badge_uid == normalized)).scalar_one_or_none()


def authenticate_by_badge(db: Session, badge_uid: str) -> User | None:
    user = get_user_by_badge_uid(db, badge_uid)
    if user is None or not user.is_active:
        return None
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(db, username)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def list_users(db: Session) -> list[User]:
    return list(db.execute(select(User).order_by(User.username)).scalars().all())


def create_user(db: Session, payload: UserCreate) -> User:
    if get_user_by_username(db, payload.username) is not None:
        raise HTTPException(status_code=409, detail=f"Username '{payload.username}' is already in use")

    user = User(
        username=payload.username.strip(),
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, payload: UserUpdate, *, acting_user: User) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == acting_user.id:
        if payload.role is not None and payload.role != UserRole.ADMIN:
            raise HTTPException(status_code=400, detail="You cannot remove your own admin role")
        if payload.is_active is False:
            raise HTTPException(status_code=400, detail="You cannot deactivate your own account")

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.password is not None:
        user.hashed_password = hash_password(payload.password)
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.badge_uid is not None:
        if payload.badge_uid == "":
            user.badge_uid = None
        else:
            normalized = normalize_badge_uid(payload.badge_uid)
            existing = get_user_by_badge_uid(db, normalized)
            if existing is not None and existing.id != user.id:
                raise HTTPException(
                    status_code=409,
                    detail=f"This badge is already assigned to '{existing.username}'",
                )
            user.badge_uid = normalized

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int, *, acting_user: User) -> None:
    if user_id == acting_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()


def seed_default_admin(db: Session) -> None:
    """
    First-run convenience: if the users table is completely empty, create a
    default admin so there's a way to log in at all. Intentionally a no-op
    otherwise, so it never resurrects a deleted/renamed account.
    """
    count = db.execute(select(func.count()).select_from(User)).scalar_one()
    if count > 0:
        return

    admin = User(
        username=settings.default_admin_username,
        full_name="Administrator",
        hashed_password=hash_password(settings.default_admin_password),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    db.commit()
