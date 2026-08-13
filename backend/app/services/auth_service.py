"""
Auth service: registration, login, password hashing, role enforcement.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import decode_access_token
from app.core.exceptions import AuthorizationError, DuplicateError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.models import AuditLog, User
from app.schemas.schemas import RegisterRequest, UserOut


def register(db: Session, req: RegisterRequest) -> User:
    existing = db.scalar(select(User).where(User.email == req.email.lower()))
    if existing:
        raise DuplicateError("An account with this email already exists")
    user = User(
        email=req.email.lower(),
        full_name=req.full_name,
        hashed_password=hash_password(req.password),
        role=req.role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(
        AuditLog(user_id=user.id, user_email=user.email, action="user_registration", target_id=str(user.id))
    )
    db.commit()
    return user


def login(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or not verify_password(password, user.hashed_password):
        raise AuthorizationError("Invalid email or password")
    if not user.is_active:
        raise AuthorizationError("Account is inactive")
    db.add(
        AuditLog(user_id=user.id, user_email=user.email, action="user_login")
    )
    db.commit()
    return user


def user_from_token(db: Session, token: str) -> User:
    payload = decode_access_token(token)
    user_id = int(payload["sub"])
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found")
    return user


def to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id, email=user.email, full_name=user.full_name, role=user.role, is_active=user.is_active
    )