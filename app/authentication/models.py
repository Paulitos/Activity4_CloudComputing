from tortoise.models import Model
from tortoise import fields
import hashlib
import secrets


class User(Model):
    id = fields.IntField(pk=True)
    external_id = fields.IntField(unique=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=100, unique=True)
    password_hash = fields.CharField(max_length=128)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    files: fields.ReverseRelation["File"]
    sessions: fields.ReverseRelation["Session"]
    
    class Meta:
        table = "users"
    
    @classmethod
    async def create_with_external_id(cls, username: str, email: str, password: str):
        """Create a user with auto-generated unique external_id"""
        # Generate unique external_id
        while True:
            external_id = secrets.randbelow(1000000000) + 1  # Generate 1 to 1 billion
            if not await cls.filter(external_id=external_id).exists():
                break
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        return await cls.create(
            external_id=external_id,
            username=username,
            email=email,
            password_hash=password_hash
        )
    
    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        return hashlib.sha256(password.encode()).hexdigest() == self.password_hash


class Session(Model):
    id = fields.IntField(pk=True)
    token = fields.CharField(max_length=64, unique=True)
    user = fields.ForeignKeyField("authentication.User", related_name="sessions")
    created_at = fields.DatetimeField(auto_now_add=True)
    expires_at = fields.DatetimeField()
    is_active = fields.BooleanField(default=True)
    
    class Meta:
        table = "sessions"
    
    @classmethod
    async def create_for_user(cls, user_id: int):
        """Create a new session token for user"""
        from datetime import datetime, timedelta
        
        token = secrets.token_hex(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        return await cls.create(
            token=token,
            user_id=user_id,
            expires_at=expires_at
        )