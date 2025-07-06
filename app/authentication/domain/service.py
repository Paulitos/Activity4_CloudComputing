from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime, timedelta
import secrets

from .entities import UserEntity, SessionEntity, RegisterInput, LoginInput
from .exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    SessionNotFoundError,
    InvalidSessionError
)


class IUserRepository(ABC):
    """Interface for user persistence"""
    
    @abstractmethod
    async def create_user(self, username: str, email: str, password: str) -> UserEntity:
        pass
    
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[UserEntity]:
        pass
    
    @abstractmethod
    async def user_exists(self, username: str, email: str) -> bool:
        pass
    
    @abstractmethod
    async def verify_password(self, username: str, password: str) -> Optional[UserEntity]:
        pass


class ISessionRepository(ABC):
    """Interface for session persistence"""
    
    @abstractmethod
    async def create_session(self, user_id: int) -> SessionEntity:
        pass
    
    @abstractmethod
    async def get_session(self, token: str) -> Optional[SessionEntity]:
        pass
    
    @abstractmethod
    async def invalidate_session(self, token: str) -> bool:
        pass
    
    @abstractmethod
    async def get_user_by_session(self, token: str) -> Optional[UserEntity]:
        pass


class AuthenticationService:
    """Domain service implementing authentication business logic"""
    
    def __init__(self, user_repo: IUserRepository, session_repo: ISessionRepository):
        self.user_repo = user_repo
        self.session_repo = session_repo
    
    async def register(self, input_data: RegisterInput) -> UserEntity:
        """Register a new user"""
        # Check if user already exists
        if await self.user_repo.user_exists(input_data.username, input_data.email):
            raise UserAlreadyExistsError("Username or email already exists")
        
        # Create user
        user = await self.user_repo.create_user(
            username=input_data.username,
            email=input_data.email,
            password=input_data.password
        )
        
        return user
    
    async def login(self, input_data: LoginInput) -> SessionEntity:
        """Authenticate user and create session"""
        # Verify credentials
        user = await self.user_repo.verify_password(
            username=input_data.username,
            password=input_data.password
        )
        
        if not user:
            raise InvalidCredentialsError("Invalid username or password")
        
        # Create session
        session = await self.session_repo.create_session(user.id)
        
        return session
    
    async def logout(self, token: str) -> bool:
        """Invalidate user session"""
        success = await self.session_repo.invalidate_session(token)
        if not success:
            raise SessionNotFoundError("Session not found or already invalidated")
        return True
    
    async def introspect(self, token: str) -> UserEntity:
        """Get user information from session token"""
        # Get session
        session = await self.session_repo.get_session(token)
        
        if not session or not session.is_active:
            raise InvalidSessionError("Invalid or expired session")
        
        # Check expiration
        if session.expires_at < datetime.utcnow():
            await self.session_repo.invalidate_session(token)
            raise InvalidSessionError("Session expired")
        
        # Get user
        user = await self.session_repo.get_user_by_session(token)
        if not user:
            raise InvalidSessionError("User not found for session")
        
        return user