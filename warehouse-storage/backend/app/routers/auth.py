"""Login and current-session endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.db import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, Token, UserOut
from app.services.user_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Validate credentials and issue a JWT used as a Bearer token on every other request."""
    user = authenticate_user(db, payload.username.strip(), payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(subject=user.username)
    return Token(access_token=access_token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    """Used by the frontend on boot to re-validate a stored token and load the user profile."""
    return current_user
