"""User management endpoints -- admin-only."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserOut, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_admin)])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return user_service.list_users(db)


@router.post("", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, payload)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    acting_user: User = Depends(require_admin),
):
    return user_service.update_user(db, user_id, payload, acting_user=acting_user)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    acting_user: User = Depends(require_admin),
):
    user_service.delete_user(db, user_id, acting_user=acting_user)
