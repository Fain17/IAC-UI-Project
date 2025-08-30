from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.service import auth_service
from typing import Optional
from jose import jwt, JWTError, ExpiredSignatureError
from app.config import SECRET_KEY, ALGORITHM
from app.db.repositories import UserRepository

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """Get current user from JWT token."""
    token = credentials.credentials
    payload = await auth_service.verify_token(token)
    
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Inactive user - account has been deactivated")
    
    # Extract role and permissions from JWT claims (not from database)
    user["role"] = payload.get("role", "viewer")
    user["permissions"] = payload.get("permissions", {})
    user["is_admin"] = payload.get("is_admin", False)
    
    return user

def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Get current active user."""
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Get current user and verify they have admin role (either permanent or temporary admin)."""
    try:
        # Check if user has admin role using the role field that's now included in user data
        user_role = current_user.get("role", "viewer")
        if user_role != "admin":
            raise HTTPException(
                status_code=403, 
                detail=f"Admin access required. User has role '{user_role}', but admin role is required."
            )
        
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        # Emergency fallback - only use is_admin for permanent admins
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")
        return current_user

async def get_user_from_token_allow_expired(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        user = await UserRepository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user - account has been deactivated")
        
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def verify_permission(required_permission: str):
    """
    Create a dependency function that verifies the required permission.
    This function returns a dependency that fetches fresh role and permission data from the database on each request.
    
    Args:
        required_permission: The permission required (read, write, execute, delete)
    
    Returns:
        A dependency function that can be used with Depends()
    """
    async def _verify_permission(current_user: dict = Depends(get_current_user)) -> dict:
        try:
            # Use permissions from JWT claims (already verified and fresh)
            user_role = current_user.get("role", "viewer")
            grouped_permissions = current_user.get("permissions", {})
            
            # Check if user has the required permission on any resource type
            has_permission = False
            for resource_type, permissions in grouped_permissions.items():
                if required_permission in permissions:
                    has_permission = True
                    break
            
            if not has_permission:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. User has role '{user_role}' with permissions {grouped_permissions}, but '{required_permission}' permission is required on any resource."
                )
            
            return current_user
            
        except HTTPException:
            raise
        except Exception as e:
            # Emergency fallback - only use is_admin for permanent admins
            if current_user.get("is_admin", False):
                # Permanent admin has all permissions on all resources
                current_user["role"] = "admin"
                current_user["permissions"] = {
                    "workflow": ["read", "write", "execute", "delete"],
                    "group": ["read", "write", "execute", "delete"]
                }
                return current_user
            else:
                # Default to viewer permissions
                current_user["role"] = "viewer"
                current_user["permissions"] = {
                    "workflow": ["read", "execute"],
                    "group": ["read"]
                }
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission verification failed. Defaulting to viewer role with limited permissions."
                )
    
    return _verify_permission

async def verify_group_read_permission(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify read permission for group management."""
    try:
        # Use permissions from JWT claims (already verified and fresh)
        user_role = current_user.get("role", "viewer")
        grouped_permissions = current_user.get("permissions", {})
        
        # Check if user has read permission on 'group' resource
        group_permissions = grouped_permissions.get("group", [])
        if "read" not in group_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions for group management. User has role '{user_role}' with group permissions {group_permissions}, but 'read' permission on 'group' resource is required."
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        # Emergency fallback - only use is_admin for permanent admins
        if current_user.get("is_admin", False):
            # Permanent admin has all permissions
            current_user["role"] = "admin"
            current_user["permissions"] = ["read", "write", "execute", "delete"]
            return current_user
        else:
            # Default to viewer permissions
            current_user["role"] = "viewer"
            current_user["permissions"] = ["read", "execute"]
            raise HTTPException(
                status_code=403,
                detail=f"Group permission verification failed. Defaulting to viewer role with limited permissions."
            )

async def verify_group_write_permission(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify write permission for group management."""
    try:
        # Use permissions from JWT claims (already verified and fresh)
        user_role = current_user.get("role", "viewer")
        grouped_permissions = current_user.get("permissions", {})
        
        # Check if user has write permission on 'group' resource
        group_permissions = grouped_permissions.get("group", [])
        if "write" not in group_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions for group management. User has role '{user_role}' with group permissions {group_permissions}, but 'write' permission on 'group' resource is required."
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        # Emergency fallback - only use is_admin for permanent admins
        if current_user.get("is_admin", False):
            # Permanent admin has all permissions
            current_user["role"] = "admin"
            current_user["permissions"] = ["read", "write", "execute", "delete"]
            return current_user
        else:
            # Default to viewer permissions
            current_user["role"] = "viewer"
            current_user["permissions"] = ["read", "execute"]
            raise HTTPException(
                status_code=403,
                detail=f"Group permission verification failed. Defaulting to viewer role with limited permissions."
            )

async def verify_group_delete_permission(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify delete permission for group management."""
    try:
        # Use permissions from JWT claims (already verified and fresh)
        user_role = current_user.get("role", "viewer")
        grouped_permissions = current_user.get("permissions", {})
        
        # Check if user has delete permission on 'group' resource
        group_permissions = grouped_permissions.get("group", [])
        if "delete" not in group_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions for group management. User has role '{user_role}' with group permissions {group_permissions}, but 'delete' permission on 'group' resource is required."
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        # Emergency fallback - only use is_admin for permanent admins
        if current_user.get("is_admin", False):
            # Permanent admin has all permissions
            current_user["role"] = "admin"
            current_user["permissions"] = ["read", "write", "execute", "delete"]
            return current_user
        else:
            # Default to viewer permissions
            current_user["role"] = "viewer"
            current_user["permissions"] = ["read", "execute"]
            raise HTTPException(
                status_code=403,
                detail=f"Group permission verification failed. Defaulting to viewer role with limited permissions."
            )

async def verify_workflow_execute_permission(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify execute permission for workflow execution."""
    try:
        # Use permissions from JWT claims (already verified and fresh)
        user_role = current_user.get("role", "viewer")
        grouped_permissions = current_user.get("permissions", {})
        
        # Check if user has execute permission on 'workflow' resource
        workflow_permissions = grouped_permissions.get("workflow", [])
        if "execute" not in workflow_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions for workflow execution. User has role '{user_role}' with workflow permissions {workflow_permissions}, but 'execute' permission on 'workflow' resource is required."
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        # Emergency fallback - only use is_admin for permanent admins
        if current_user.get("is_admin", False):
            # Permanent admin has all permissions
            current_user["role"] = "admin"
            current_user["permissions"] = ["read", "write", "execute", "delete"]
            return current_user
        else:
            # Default to viewer permissions
            current_user["role"] = "viewer"
            current_user["permissions"] = ["read", "execute"]
            raise HTTPException(
                status_code=403,
                detail=f"Workflow execution permission verification failed. Defaulting to viewer role with limited permissions."
            )

async def verify_workflow_read_permission(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify read permission for workflow access."""
    try:
        # Use permissions from JWT claims (already verified and fresh)
        user_role = current_user.get("role", "viewer")
        grouped_permissions = current_user.get("permissions", {})
        
        # Check if user has read permission on 'workflow' resource
        workflow_permissions = grouped_permissions.get("workflow", [])
        if "read" not in workflow_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions for workflow access. User has role '{user_role}' with workflow permissions {workflow_permissions}, but 'read' permission on 'workflow' resource is required."
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        # Emergency fallback - only use is_admin for permanent admins
        if current_user.get("is_admin", False):
            # Permanent admin has all permissions
            current_user["role"] = "admin"
            current_user["permissions"] = ["read", "write", "execute", "delete"]
            return current_user
        else:
            # Default to viewer permissions
            current_user["role"] = "viewer"
            current_user["permissions"] = ["read", "execute"]
            raise HTTPException(
                status_code=403,
                detail=f"Workflow read permission verification failed. Defaulting to viewer role with limited permissions."
            )

async def verify_config_read_permission(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify read permission for config access."""
    try:
        # Use permissions from JWT claims (already verified and fresh)
        user_role = current_user.get("role", "viewer")
        grouped_permissions = current_user.get("permissions", {})
        
        # Check if user has read permission on 'config' resource
        config_permissions = grouped_permissions.get("config", [])
        if "read" not in config_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions for config access. User has role '{user_role}' with config permissions {config_permissions}, but 'read' permission on 'config' resource is required."
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        # Emergency fallback - only use is_admin for permanent admins
        if current_user.get("is_admin", False):
            # Permanent admin has all permissions
            current_user["role"] = "admin"
            current_user["permissions"] = ["read", "write", "delete"]
            return current_user
        else:
            # Default to viewer permissions
            current_user["role"] = "viewer"
            current_user["permissions"] = ["read"]
            raise HTTPException(
                status_code=403,
                detail=f"Config read permission verification failed. Defaulting to viewer role with limited permissions."
            )

async def verify_config_write_permission(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify write permission for config management."""
    try:
        # Use permissions from JWT claims (already verified and fresh)
        user_role = current_user.get("role", "viewer")
        grouped_permissions = current_user.get("permissions", {})
        
        # Check if user has write permission on 'config' resource
        config_permissions = grouped_permissions.get("config", [])
        if "write" not in config_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions for config management. User has role '{user_role}' with config permissions {config_permissions}, but 'write' permission on 'config' resource is required."
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        # Emergency fallback - only use is_admin for permanent admins
        if current_user.get("is_admin", False):
            # Permanent admin has all permissions
            current_user["role"] = "admin"
            current_user["permissions"] = ["read", "write", "delete"]
            return current_user
        else:
            # Default to viewer permissions
            current_user["role"] = "viewer"
            current_user["permissions"] = ["read"]
            raise HTTPException(
                status_code=403,
                detail=f"Config write permission verification failed. Defaulting to viewer role with limited permissions."
            )

async def verify_config_delete_permission(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify delete permission for config management."""
    try:
        # Use permissions from JWT claims (already verified and fresh)
        user_role = current_user.get("role", "viewer")
        grouped_permissions = current_user.get("permissions", {})
        
        # Check if user has delete permission on 'config' resource
        config_permissions = grouped_permissions.get("config", [])
        if "delete" not in config_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions for config management. User has role '{user_role}' with config permissions {config_permissions}, but 'delete' permission on 'config' resource is required."
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        # Emergency fallback - only use is_admin for permanent admins
        if current_user.get("is_admin", False):
            # Permanent admin has all permissions
            current_user["role"] = "admin"
            current_user["permissions"] = ["read", "write", "delete"]
            return current_user
        else:
            # Default to viewer permissions
            current_user["role"] = "viewer"
            current_user["permissions"] = ["read"]
            raise HTTPException(
                status_code=403,
                detail=f"Config delete permission verification failed. Defaulting to viewer role with limited permissions."
            )

async def get_user_info_from_token(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Get current user information including role and admin status from JWT claims.
    This function extracts role and admin information that was embedded in the JWT token.
    
    Returns:
        User dictionary with role and admin information extracted from JWT
    """
    try:
        # The role and admin information is already embedded in the JWT token
        # and extracted by get_current_user dependency
        user_role = current_user.get("role", "viewer")
        is_admin = current_user.get("is_admin", False)
        
        # Add role type classification for frontend convenience
        if is_admin:
            role_type = "permanent_admin"
        elif user_role == "admin":
            role_type = "temporary_admin"
        else:
            role_type = "regular_user"
        
        # Return enriched user data
        return {
            **current_user,
            "role": user_role,
            "role_type": role_type,
            "is_admin": is_admin
        }
        
    except Exception as e:
        logger.error(f"Error extracting user info from token: {e}")
        # Return basic user data if extraction fails
        return current_user 