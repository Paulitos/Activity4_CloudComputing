class AuthenticationError(Exception):
    """Base exception for authentication errors"""
    pass


class UserAlreadyExistsError(AuthenticationError):
    """Raised when trying to register an existing user"""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid"""
    pass


class SessionNotFoundError(AuthenticationError):
    """Raised when session is not found"""
    pass


class InvalidSessionError(AuthenticationError):
    """Raised when session is invalid or expired"""
    pass