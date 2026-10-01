import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    full_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one letter and one number")
        return value


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
