from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UserEntity:
    """Domain entity representing a user"""
    external_id: int
    username: str
    email: str
    created_at: datetime
    updated_at: datetime
    id: Optional[int] = None


@dataclass
class SessionEntity:
    """Domain entity representing a user session"""
    token: str
    user_id: int
    created_at: datetime
    expires_at: datetime
    is_active: bool
    id: Optional[int] = None
    

@dataclass
class RegisterInput:
    """Input for user registration"""
    username: str
    email: str
    password: str


@dataclass
class LoginInput:
    """Input for user login"""
    username: str
    password: str