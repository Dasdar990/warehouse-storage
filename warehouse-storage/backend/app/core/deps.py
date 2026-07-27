"""FastAPI dependencies for authentication and authorization."""
from typing import Optional

from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db import get_db
from app.models.user import User, UserRole
from app.services.user_service import get_user_by_username

# auto_error=False so we can also accept the token via query string (see
# below) for the label print link, which opens as a plain browser
# navigation and can't attach an Authorization header.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    token: Optional[str] = Query(default=None, description="Bearer token, as a fallback for plain-navigation links"),
    db: Session = Depends(get_db),
) -> User:
    raw_token = credentials.credentials if credentials else token
    if not raw_token:
        raise HTTPException(status_code=401, detail="Autenticazione richiesta")

    payload = decode_access_token(raw_token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = get_user_by_username(db, payload["sub"])
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or deactivated user")

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Richiesti permessi di amministratore")
    return current_user
