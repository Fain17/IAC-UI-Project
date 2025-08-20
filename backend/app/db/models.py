from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Script Type Enum
class ScriptType(str, Enum):
    PYTHON = "python"
    NODEJS = "nodejs"

# Role and Permission Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"

class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"

# Role-Permission Mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.DELETE],
    UserRole.MANAGER: [Permission.READ, Permission.WRITE, Permission.EXECUTE],
    UserRole.VIEWER: [Permission.READ, Permission.EXECUTE]
}

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
    id: str
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
    user_id: Optional[str] = None

# Session Models
class UserSessionBase(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime

class UserSession(UserSessionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Refresh Token Models
class RefreshTokenBase(BaseModel):
    user_id: str
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
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserPermissionBase(BaseModel):
    user_id: str
    role: UserRole  # admin, manager, viewer

class UserPermissionCreate(UserPermissionBase):
    pass

class UserPermissionUpdate(BaseModel):
    role: UserRole

class UserPermission(UserPermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# New model for granular user permissions
class UserPermissionsBase(BaseModel):
    user_id: str
    permission: Permission
    resource_type: str  # workflow, user, group, etc.
    resource_id: Optional[str] = None  # specific resource ID, null for global permissions

class UserPermissionsCreate(UserPermissionsBase):
    pass

class UserPermissionsUpdate(BaseModel):
    permission: Permission
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None

class UserPermissions(UserPermissionsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserGroupAssignmentBase(BaseModel):
    user_id: str
    group_id: str

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
    role: UserRole = UserRole.VIEWER  # admin, manager, viewer
    group_id: Optional[str] = None

class AdminUserPermissionUpdate(BaseModel):
    role: Optional[UserRole] = None
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
    user_id: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 

# HashiCorp Vault Configuration Models
class VaultEngineType(str, Enum):
    KV = "kv"
    AWS = "aws"
    AZURE = "azure"
    GOOGLE_CLOUD = "google_cloud"

class VaultEngineVersion(str, Enum):
    V1 = "1"
    V2 = "2"

class VaultConfigBase(BaseModel):
    config_name: str
    vault_address: str
    vault_token: str
    namespace: Optional[str] = None
    mount_path: str
    engine_type: VaultEngineType
    engine_version: VaultEngineVersion
    is_active: bool = True

class VaultConfigCreate(VaultConfigBase):
    pass

class VaultConfigUpdate(BaseModel):
    config_name: Optional[str] = None
    vault_address: Optional[str] = None
    vault_token: Optional[str] = None
    namespace: Optional[str] = None
    mount_path: Optional[str] = None
    engine_type: Optional[VaultEngineType] = None
    engine_version: Optional[VaultEngineVersion] = None
    is_active: Optional[bool] = None

class VaultConfig(VaultConfigBase):
    id: int
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 