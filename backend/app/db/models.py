from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Config Mapping Models
class ConfigMappingBase(BaseModel):
    instance_name: str
    launch_template_name: str

class ConfigMappingCreate(ConfigMappingBase):
    pass

class ConfigMappingUpdate(BaseModel):
    launch_template_name: str

class ConfigMapping(ConfigMappingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# User Models
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Authentication Models
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class TokenData(BaseModel):
    user_id: Optional[int] = None

# Session Models
class UserSessionBase(BaseModel):
    user_id: int
    session_token: str
    expires_at: datetime

class UserSession(UserSessionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True 