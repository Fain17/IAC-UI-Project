from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Script Type Enum
class ScriptType(str, Enum):
    PYTHON = "python"
    NODEJS = "nodejs"

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

# User Management Models
class UserGroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class UserGroupCreate(UserGroupBase):
    pass

class UserGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class UserGroup(UserGroupBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserPermissionBase(BaseModel):
    user_id: int
    permission_level: str  # admin, manager, viewer

class UserPermissionCreate(UserPermissionBase):
    pass

class UserPermissionUpdate(BaseModel):
    permission_level: str

class UserPermission(UserPermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserGroupAssignmentBase(BaseModel):
    user_id: int
    group_id: int

class UserGroupAssignmentCreate(UserGroupAssignmentBase):
    pass

class UserGroupAssignment(UserGroupAssignmentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AdminUserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    permission_level: str = "viewer"  # admin, manager, viewer
    group_id: Optional[int] = None

class AdminUserPermissionUpdate(BaseModel):
    permission_level: Optional[str] = None
    is_active: Optional[bool] = None

# Workflow Models

class WorkflowStep(BaseModel):
    """Model for updating workflow steps (excludes id field)."""
    name: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None  # Position in the workflow (1-based)
    script_type: Optional[ScriptType] = None  # python, nodejs
    script_filename: Optional[str] = None
    run_command: Optional[str] = None
    dependencies: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    steps: List[WorkflowStep] = []

class WorkflowCreateRequest(BaseModel):
    """Model for creating a new workflow (JSON input)."""
    name: str
    description: Optional[str] = None

class WorkflowCreate(WorkflowBase):
    pass

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[WorkflowStep]] = None
    is_active: Optional[bool] = None

class Workflow(WorkflowBase):
    id: str  # UUID for workflow
    user_id: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 