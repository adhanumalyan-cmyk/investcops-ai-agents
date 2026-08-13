"""Auth routes: register, login (OAuth2 password flow), current user."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, get_current_user
from app.core.exceptions import AuthorizationError, DuplicateError
from app.database.session import get_db
from app.models.models import User
from app.schemas.schemas import RegisterRequest, TokenResponse, UserOut
from app.services.auth_service import login, register, to_user_out

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_endpoint(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register(db, req)
    except DuplicateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    token = create_access_token(user)
    return TokenResponse(access_token=token, user=to_user_out(user))


@router.post("/login", response_model=TokenResponse)
def login_endpoint(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = login(db, form.username, form.password)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    token = create_access_token(user)
    return TokenResponse(access_token=token, user=to_user_out(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return to_user_out(current_user)