"""Authentication routes."""

import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from psycopg.rows import dict_row

from api.models.auth import Token, User, UserCreate
from core.auth import (
    create_access_token,
    get_password_hash,
    verify_password,
    decode_access_token
)
from core.database import get_conn

logger = logging.getLogger(__name__)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """Dependency to get the currently authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user_data = cur.fetchone()
            if user_data is None:
                raise credentials_exception
            return User(**user_data)


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate):
    """Register a new user."""
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # Check if user already exists
            cur.execute("SELECT 1 FROM users WHERE username = %s", (user_in.username,))
            if cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered"
                )
            
            hashed_pw = get_password_hash(user_in.password)
            cur.execute(
                "INSERT INTO users (username, hashed_password, email) VALUES (%s, %s, %s) RETURNING *",
                (user_in.username, hashed_pw, user_in.email)
            )
            new_user = cur.fetchone()
            conn.commit()
            return User(**new_user)


@router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Login and get access token."""
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (form_data.username,))
            user = cur.fetchone()
            
            if not user or not verify_password(form_data.password, user["hashed_password"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            access_token = create_access_token(data={"sub": user["username"]})
            return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current user information."""
    return current_user
