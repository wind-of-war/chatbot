from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from apps.api.database import engine, get_db
from apps.api.database_migrations import ensure_user_schema_columns
from apps.api.middleware.auth import create_access_token, hash_password, safe_decode_token, verify_password
from apps.api.models import User
from apps.api.schemas import LoginRequest, RegisterRequest, TokenResponse
from configs.settings import settings


security = HTTPBearer(auto_error=True)


def _is_admin_email(email: str) -> bool:
    admin_emails = [item.strip().lower() for item in settings.admin_emails.split(",") if item.strip()]
    return email.lower() in admin_emails


def _ensure_schema() -> None:
    ensure_user_schema_columns(engine)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    _ensure_schema()

    payload = safe_decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def register_user(payload: RegisterRequest, db: Session) -> TokenResponse:
    _ensure_schema()

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    role = "admin" if _is_admin_email(payload.email) else "user"
    user = User(email=payload.email, password_hash=hash_password(payload.password), plan="free", role=role, status="active")
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(str(user.id)), user_id=user.id, role=user.role, status=user.status)


def login_user(payload: LoginRequest, db: Session) -> TokenResponse:
    _ensure_schema()

    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")
    return TokenResponse(access_token=create_access_token(str(user.id)), user_id=user.id, role=user.role, status=user.status)
