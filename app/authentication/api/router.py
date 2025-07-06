from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel, EmailStr

from app.authentication.dependency_injection.container import auth_container
from app.authentication.domain import (
    RegisterInput,
    LoginInput,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    SessionNotFoundError,
    InvalidSessionError
)


router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    external_id: int
    username: str
    email: str


class LoginResponse(BaseModel):
    token: str
    user: UserResponse


class StatusResponse(BaseModel):
    status: str
    message: str = ""


@router.post("/register", response_model=StatusResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        input_data = RegisterInput(
            username=request.username,
            email=request.email,
            password=request.password
        )
        
        user = await auth_container.auth_service.register(input_data)
        
        return StatusResponse(
            status="success",
            message=f"User {user.username} created successfully"
        )
    
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login user and create session"""
    try:
        input_data = LoginInput(
            username=request.username,
            password=request.password
        )
        
        session = await auth_container.auth_service.login(input_data)
        
        # Get user info for response
        user = await auth_container.auth_service.introspect(session.token)
        
        return LoginResponse(
            token=session.token,
            user=UserResponse(
                external_id=user.external_id,
                username=user.username,
                email=user.email
            )
        )
    
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/logout", response_model=StatusResponse)
async def logout(auth: str = Header(alias="Auth")):
    """Logout user and invalidate session"""
    try:
        await auth_container.auth_service.logout(auth)
        
        return StatusResponse(
            status="success",
            message="Logged out successfully"
        )
    
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/introspect", response_model=UserResponse)
async def introspect(auth: str = Header(alias="Auth")):
    """Get user information from session token"""
    try:
        user = await auth_container.auth_service.introspect(auth)
        
        return UserResponse(
            external_id=user.external_id,
            username=user.username,
            email=user.email
        )
    
    except InvalidSessionError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )