from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.api.rate_limit import client_ip, enforce_rate_limit
from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    spend_verify_time,
    verify_password,
)
from app.models import User
from app.schemas.auth import Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

_EMAIL_TAKEN = "An account with this email already exists"


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession, request: Request, response: Response):
    enforce_rate_limit(
        request,
        response,
        key=f"rl:register:ip:{client_ip(request)}",
        limit=settings.RATE_LIMIT_REGISTER_IP,
        window_seconds=settings.RATE_LIMIT_REGISTER_WINDOW_SECONDS,
        fail_closed=True,
        detail="Too many accounts created from this network. Try again in {retry_after} seconds.",
    )
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_EMAIL_TAKEN)

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Two sign-ups with the same email raced past the check above.
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_EMAIL_TAKEN)
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
    request: Request,
    response: Response,
):
    """OAuth2 password flow: `username` is the user's email."""
    ip = client_ip(request)
    email = form.username.strip().lower()
    enforce_rate_limit(
        request,
        response,
        key=f"rl:login:ip:{ip}",
        limit=settings.RATE_LIMIT_LOGIN_IP,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
        fail_closed=True,
        detail="Too many login attempts. Try again in {retry_after} seconds.",
    )
    enforce_rate_limit(
        request,
        response,
        key=f"rl:login:email:{email}",
        limit=settings.RATE_LIMIT_LOGIN_EMAIL,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
        fail_closed=True,
        detail="Too many login attempts. Try again in {retry_after} seconds.",
    )
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={
            "WWW-Authenticate": "Bearer",
            **{
                name: value
                for name in ("X-RateLimit-Limit", "X-RateLimit-Remaining")
                if (value := response.headers.get(name))
            },
        },
    )
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        spend_verify_time(form.password)
        raise invalid
    if not verify_password(form.password, user.hashed_password) or not user.is_active:
        raise invalid

    token, expires_in = create_access_token(subject=str(user.id), role=user.role)
    return Token(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UserOut)
def me(current_user: CurrentUser):
    return current_user
