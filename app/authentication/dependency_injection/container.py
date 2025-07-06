from app.authentication.domain.service import AuthenticationService
from app.authentication.persistence.repository import UserRepository
from app.authentication.persistence.redis_repository import RedisSessionRepository


class AuthenticationContainer:
    """Dependency injection container for authentication module"""
    
    _instance = None
    _auth_service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def auth_service(self) -> AuthenticationService:
        """Get authentication service singleton"""
        if self._auth_service is None:
            user_repo = UserRepository()
            session_repo = RedisSessionRepository()
            self._auth_service = AuthenticationService(user_repo, session_repo)
        return self._auth_service


# Global instance
auth_container = AuthenticationContainer()