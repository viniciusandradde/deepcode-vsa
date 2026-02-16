"""Authentication Pydantic models."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user properties."""
    username: str
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    """User creation model."""
    password: str


class User(UserBase):
    """User in database."""
    id: int
    org_id: Optional[UUID] = None
    role: str = "user"
    display_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Authentication token response."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
