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

# Refresh Token Models
class RefreshTokenBase(BaseModel):
    user_id: int
    refresh_token: str
    expires_at: datetime

class RefreshToken(RefreshTokenBase):
    id: int
    is_revoked: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: dict

# Workflow Models
class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    steps: list  # List of workflow steps/actions
    is_active: bool = True
    script_type: Optional[str] = None  # sh, playbook, terraform, aws, etc.
    script_content: Optional[str] = None  # The actual code/script content
    script_filename: Optional[str] = None  # Original filename if uploaded

class WorkflowCreate(WorkflowBase):
    pass

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[list] = None
    is_active: Optional[bool] = None
    script_type: Optional[str] = None
    script_content: Optional[str] = None
    script_filename: Optional[str] = None

class Workflow(WorkflowBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Script Execution Models
class ScriptExecutionRequest(BaseModel):
    workflow_id: int
    parameters: Optional[dict] = None  # Parameters to pass to the script
    environment: Optional[dict] = None  # Environment variables

class ScriptExecutionResponse(BaseModel):
    execution_id: str
    status: str  # running, completed, failed
    output: Optional[str] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time: Optional[float] = None 