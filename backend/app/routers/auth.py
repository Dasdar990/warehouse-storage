"""Login and current-session endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.db import get_db
from app.models.user import User
from app.schemas.auth import BadgeLoginRequest, LoginRequest, Token, UserOut
from app.services.user_service import authenticate_by_badge, authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Validate credentials and issue a JWT used as a Bearer token on every other request."""
    user = authenticate_user(db, payload.username.strip(), payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(subject=user.username)
    return Token(access_token=access_token, user=UserOut.model_validate(user))


@router.post("/badge-login", response_model=Token)
def badge_login(payload: BadgeLoginRequest, db: Session = Depends(get_db)):
    """
    Same as /login but authenticates by a scanned NFC badge UID instead of
    username/password. Issues the exact same kind of JWT, so nothing else
    downstream (deps, frontend token storage) needs to know how the session
    started.
    """
    user = authenticate_by_badge(db, payload.badge_uid)
    if user is None:
        raise HTTPException(status_code=401, detail="Unrecognized or inactive badge")

    access_token = create_access_token(subject=user.username)
    return Token(access_token=access_token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    """Used by the frontend on boot to re-validate a stored token and load the user profile."""
    return current_user
