from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.service import auth_service
from typing import Optional
from jose import jwt, JWTError, ExpiredSignatureError
from app.config import SECRET_KEY, ALGORITHM
from app.db.repositories import UserRepository, UserPermissionRepository

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
    
    # Enrich user data with role information from permissions table
    try:
        user_permissions = await UserPermissionRepository.get_by_user_id(user_id)
        if user_permissions:
            user["role"] = user_permissions.get("role", "viewer")
        else:
            # If no permissions found, default to viewer role
            user["role"] = "viewer"
    except Exception as e:
        # If there's an error getting permissions, default to viewer role
        user["role"] = "viewer"
    
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
            # Always fetch fresh role and permission data from database
            user_permission = await UserPermissionRepository.get_by_user_id(current_user["id"])
            user_role = user_permission.get("role", "viewer") if user_permission else "viewer"
            
            # Get permissions for this role from the database instead of hardcoded model
            from app.db.repositories import RolePermissionRepository
            db_permissions = await RolePermissionRepository.get_by_role(user_role)
            
            # Extract permission names from database results
            user_permissions = []
            for perm in db_permissions:
                user_permissions.append(perm["permission"])
            
            # Check if user has the required permission
            if required_permission not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. User has role '{user_role}' with permissions {user_permissions}, but '{required_permission}' permission is required."
                )
            
            # Update the current_user with fresh role and permission data
            current_user["role"] = user_role
            current_user["permissions"] = user_permissions
            
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
                    detail=f"Permission verification failed. Defaulting to viewer role with limited permissions."
                )
    
    return _verify_permission

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