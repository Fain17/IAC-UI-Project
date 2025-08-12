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
    
    return user

def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Get current active user."""
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Get current user and verify they have admin role (either permanent or temporary admin)."""
    try:
        # Check if user has admin role in permissions (this covers both permanent and temporary admins)
        user_permissions = await UserPermissionRepository.get_by_user_id(current_user["id"])
        
        if not user_permissions or user_permissions.get("role") != "admin":
            raise HTTPException(
                status_code=403, 
                detail="Admin access required. User must have admin role in permissions."
            )
        
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        # If there's an error checking permissions, fall back to checking is_admin column
        # This provides backward compatibility
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