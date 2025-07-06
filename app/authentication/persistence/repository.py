from typing import Optional
from datetime import datetime

from app.authentication.models import User, Session
from app.authentication.domain.entities import UserEntity, SessionEntity
from app.authentication.domain.service import IUserRepository, ISessionRepository


class UserRepository(IUserRepository):
    """Tortoise ORM implementation of user repository"""
    
    async def create_user(self, username: str, email: str, password: str) -> UserEntity:
        """Create a new user"""
        user = await User.create_with_external_id(
            username=username,
            email=email,
            password=password
        )
        
        return UserEntity(
            id=user.id,
            external_id=user.external_id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    async def get_user_by_username(self, username: str) -> Optional[UserEntity]:
        """Get user by username"""
        user = await User.filter(username=username).first()
        if not user:
            return None
        
        return UserEntity(
            id=user.id,
            external_id=user.external_id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    async def user_exists(self, username: str, email: str) -> bool:
        """Check if user exists by username or email"""
        return await User.filter(username=username).exists() or \
               await User.filter(email=email).exists()
    
    async def verify_password(self, username: str, password: str) -> Optional[UserEntity]:
        """Verify user password and return user if valid"""
        user = await User.filter(username=username).first()
        if not user or not user.verify_password(password):
            return None
        
        return UserEntity(
            id=user.id,
            external_id=user.external_id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at
        )


class SessionRepository(ISessionRepository):
    """Tortoise ORM implementation of session repository"""
    
    async def create_session(self, user_id: int) -> SessionEntity:
        """Create a new session for user"""
        session = await Session.create_for_user(user_id)
        
        return SessionEntity(
            id=session.id,
            token=session.token,
            user_id=session.user_id,
            created_at=session.created_at,
            expires_at=session.expires_at,
            is_active=session.is_active
        )
    
    async def get_session(self, token: str) -> Optional[SessionEntity]:
        """Get session by token"""
        session = await Session.filter(token=token).first()
        if not session:
            return None
        
        return SessionEntity(
            id=session.id,
            token=session.token,
            user_id=session.user_id,
            created_at=session.created_at,
            expires_at=session.expires_at,
            is_active=session.is_active
        )
    
    async def invalidate_session(self, token: str) -> bool:
        """Invalidate a session"""
        session = await Session.filter(token=token, is_active=True).first()
        if not session:
            return False
        
        session.is_active = False
        await session.save()
        return True
    
    async def get_user_by_session(self, token: str) -> Optional[UserEntity]:
        """Get user associated with session"""
        session = await Session.filter(token=token, is_active=True).first()
        if not session:
            return None
        
        user = await session.user
        if not user:
            return None
        
        return UserEntity(
            id=user.id,
            external_id=user.external_id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at
        )