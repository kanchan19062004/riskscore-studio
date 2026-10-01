from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings

_hasher = PasswordHasher()

# Verified against when the email doesn't exist, so "unknown email" and
# "wrong password" take the same time and can't be told apart by timing.
_DUMMY_HASH = _hasher.hash("timing-equalizer")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return _hasher.verify(hashed_password, password)
    except (VerificationError, InvalidHashError):
        return False


def spend_verify_time(password: str) -> None:
    verify_password(password, _DUMMY_HASH)


def create_access_token(subject: str, role: str) -> tuple[str, int]:
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expires_in


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["exp", "sub"]},
    )
