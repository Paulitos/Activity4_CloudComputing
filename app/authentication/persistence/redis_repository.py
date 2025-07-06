import json
import os
from typing import Optional
from datetime import datetime
import redis.asyncio as redis

from app.authentication.domain.entities import UserEntity, SessionEntity
from app.authentication.domain.service import ISessionRepository
from app.authentication.models import User


class RedisSessionRepository(ISessionRepository):
    """Redis implementation of session repository"""
    
    def __init__(self):
        self._redis_client = None
        self._redis_host = os.getenv("REDIS_HOST", "localhost")
        self._redis_port = int(os.getenv("REDIS_PORT", 6379))
    
    async def _get_redis(self):
        """Get Redis client (lazy initialization)"""
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host=self._redis_host,
                port=self._redis_port,
                decode_responses=True
            )
        return self._redis_client
    
    async def create_session(self, user_id: int) -> SessionEntity:
        """Create a new session for user"""
        import secrets
        from datetime import datetime, timedelta
        
        token = secrets.token_hex(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Get user to store in session
        user = await User.filter(id=user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        session = SessionEntity(
            token=token,
            user_id=user_id,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            is_active=True
        )
        
        # Store session in Redis with expiration
        redis_client = await self._get_redis()
        session_data = {
            "user_id": user_id,
            "user_external_id": user.external_id,
            "username": user.username,
            "email": user.email,
            "created_at": session.created_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "is_active": True
        }
        
        # Set expiration to 24 hours
        await redis_client.setex(
            f"session:{token}",
            24 * 3600,  # 24 hours in seconds
            json.dumps(session_data)
        )
        
        return session
    
    async def get_session(self, token: str) -> Optional[SessionEntity]:
        """Get session by token"""
        redis_client = await self._get_redis()
        session_data = await redis_client.get(f"session:{token}")
        
        if not session_data:
            return None
        
        data = json.loads(session_data)
        
        return SessionEntity(
            token=token,
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            is_active=data["is_active"]
        )
    
    async def invalidate_session(self, token: str) -> bool:
        """Invalidate a session"""
        redis_client = await self._get_redis()
        
        # Check if session exists
        session_data = await redis_client.get(f"session:{token}")
        if not session_data:
            return False
        
        # Delete session from Redis
        await redis_client.delete(f"session:{token}")
        return True
    
    async def get_user_by_session(self, token: str) -> Optional[UserEntity]:
        """Get user associated with session"""
        redis_client = await self._get_redis()
        session_data = await redis_client.get(f"session:{token}")
        
        if not session_data:
            return None
        
        data = json.loads(session_data)
        
        # Get fresh user data from database
        user = await User.filter(id=data["user_id"]).first()
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