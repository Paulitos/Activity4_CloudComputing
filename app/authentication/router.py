from fastapi import APIRouter, Body, HTTPException, Header
from typing import Union
import uuid
import hashlib
from pydantic import BaseModel
from app.authentication.models import User, Session

router = APIRouter()

class RegisterAPIInput(BaseModel):
    username: str
    password: str
    mail: str

@router.post("/register")
async def register(input_body: RegisterAPIInput = Body()) -> dict[str, Union[str, int]]:
    # Check if user already exists
    if await User.filter(username=input_body.username).exists() or \
       await User.filter(email=input_body.mail).exists():
        raise HTTPException(status_code=409, detail="User already exists")
    
    # Create user with external_id
    user = await User.create_with_external_id(
        username=input_body.username,
        email=input_body.mail,
        password=input_body.password
    )
    
    return {
        "external_id": user.external_id,
        "username": user.username,
        "mail": user.email
    }

class LoginAPIInput(BaseModel):
    username: str
    password: str
    mail: str

@router.post("/login")
async def login(input_body: LoginAPIInput = Body()) -> dict[str, str]:
    user = await User.filter(username=input_body.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.verify_password(input_body.password):
        raise HTTPException(status_code=401, detail="Login data is incorrect")

    # Create session
    session = await Session.create_for_user(user.id)
    return {"auth": session.token}

@router.get("/introspect")
async def introspect(auth_token: str = Header(alias="auth")) -> dict[str, Union[str, int]]:
    session = await Session.filter(token=auth_token, is_active=True).first()
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = await session.user
    return {
        "username": user.username,
        "mail": user.email,
        "external_id": user.external_id
    }

@router.post("/logout")
async def logout(auth_token: str = Header(alias="auth")) -> dict[str, str]:
    session = await Session.filter(token=auth_token, is_active=True).first()
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    session.is_active = False
    await session.save()
    
    return {
        "status": "ok",
        "message": "Logout successful"
    }