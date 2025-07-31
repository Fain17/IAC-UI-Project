import re
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from app.auth.service import auth_service
from app.auth.dependencies import get_current_user
from typing import Optional
import secrets
from app.auth.dependencies import get_user_from_token_allow_expired


router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: dict
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

class EditUsernameRequest(BaseModel):
    new_username: str

class DeleteAccountRequest(BaseModel):
    password: str

class RequestPasswordReset(BaseModel):
    email: str

class HardResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

class TokenVerificationResponse(BaseModel):
    valid: bool
    user: Optional[dict] = None
    error: Optional[str] = None
    expires_at: Optional[str] = None
    time_remaining_seconds: Optional[int] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token to use for getting new access token")

def is_email(value: str) -> bool:
    """Check if the input looks like an email address."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, value))

@router.post("/register", response_model=dict)
async def register(user_data: UserRegister):
    """Register a new user."""
    result = await auth_service.register_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"message": result["message"]}

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Login user and return JWT access token + refresh token."""
    # Determine if input is email or username
    if is_email(user_data.username_or_email):
        user = await auth_service.authenticate_user_by_email(user_data.username_or_email, user_data.password)
    else:
        user = await auth_service.authenticate_user(user_data.username_or_email, user_data.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create both access and refresh tokens
    tokens = await auth_service.login_user(user)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user=tokens["user"]
    )
    
@router.post("/change-password", response_model=dict)
async def change_password(
    data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    result = await auth_service.change_password(
        user_id=current_user["id"],
        current_password=data.current_password,
        new_password=data.new_password,
        confirm_password=data.confirm_password
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": result["message"]}

@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return current_user



@router.get("/verify-token", response_model=TokenVerificationResponse, summary="Verify Current User's Token")
async def verify_token_get(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Verify the current user's access token and get session information.
    
    **Usage:**
    - Requires authentication (Bearer token in Authorization header)
    - Returns current user information and token expiration details
    - Useful for frontend to check token validity and remaining time
    
    **Security:**
    - Only authenticated users can access this endpoint
    - Prevents unauthorized token testing
    - Returns information only for the authenticated user's token
    """
    try:
        # Get the token from the current user's session
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return TokenVerificationResponse(valid=False, error="No valid authorization header")
        
        token = auth_header.split(" ")[1]
        
        # Get session info to get expiration details
        session_info = await auth_service.get_session_info_for_token(token)
        
        if session_info is None:
            return TokenVerificationResponse(valid=False, error="Token not found in database")
        
        # Verify the token matches the current user
        payload = await auth_service.verify_token(token)
        
        if payload is None:
            return TokenVerificationResponse(
                valid=False, 
                error="Invalid token",
                expires_at=session_info["expires_at"],
                time_remaining_seconds=session_info["time_remaining_seconds"]
            )
        
        # Double-check that the token belongs to the current user
        token_user_id = payload.get("sub")
        if str(token_user_id) != str(current_user["id"]):
            return TokenVerificationResponse(
                valid=False, 
                error="Token does not belong to current user",
                expires_at=session_info["expires_at"],
                time_remaining_seconds=session_info["time_remaining_seconds"]
            )
        
        return TokenVerificationResponse(
            valid=True, 
            user=current_user,
            expires_at=session_info["expires_at"],
            time_remaining_seconds=session_info["time_remaining_seconds"]
        )
    
    except Exception as e:
        return TokenVerificationResponse(valid=False, error=f"Token verification failed: {str(e)}")

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    success = await auth_service.logout(token)
    if not success:
        raise HTTPException(status_code=400, detail="Logout failed or session not found.")
    return {"message": "Logged out successfully."} 

@router.delete("/delete-account", response_model=dict)
async def delete_account(
    data: DeleteAccountRequest,
    current_user: dict = Depends(get_current_user)
):
    result = await auth_service.delete_user_account(user_id=current_user["id"], password=data.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": result["message"]}

@router.put("/edit-username", response_model=dict)
async def edit_username(
    data: EditUsernameRequest,
    current_user: dict = Depends(get_current_user)
):
    result = await auth_service.edit_username(user_id=current_user["id"], new_username=data.new_username)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": result["message"]} 

@router.post("/request-password-reset", response_model=dict)
async def request_password_reset(data: RequestPasswordReset):
    result = await auth_service.request_password_reset(email=data.email)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": result["message"]}

@router.post("/hard-reset-password", response_model=dict)
async def hard_reset_password(data: HardResetPasswordRequest):
    result = await auth_service.hard_reset_password(
        token=data.token,
        new_password=data.new_password,
        confirm_password=data.confirm_password
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": result["message"]}

@router.get("/check-first-user", response_model=dict)
async def check_first_user():
    from app.db.database import db_service
    if not db_service.client:
        raise HTTPException(status_code=500, detail="Database client not initialized")
    result = await db_service.client.execute("SELECT COUNT(*) FROM users")
    is_first_user = result.rows[0][0] == 0
    return {"is_first_user": is_first_user} 

@router.get("/check-availability", response_model=dict)
async def check_availability(
    username: Optional[str] = Query(None),
    email: Optional[str] = Query(None)
):
    """Check if username or email is available."""
    if username:
        # Check username availability
        from app.db.repositories import UserRepository
        user = await UserRepository.get_by_username(username)
        return {"available": user is None}
    elif email:
        # Check email availability
        from app.db.repositories import UserRepository
        user = await UserRepository.get_by_email(email)
        return {"available": user is None}
    else:
        raise HTTPException(status_code=400, detail="Must provide username or email")

@router.post("/refresh-token", response_model=TokenResponse, summary="Refresh Access Token")
async def refresh(
    refresh_data: RefreshTokenRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Refresh access token using refresh token.
    
    **Usage:**
    - Requires valid Authorization header (non-expired access token required)
    - Send refresh token in request body
    - Returns new access token (same refresh token is kept)
    - Useful for getting new access tokens before current one expires
    
    **Request Body:**
    ```json
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
    
    **Security:**
    - Only authenticated users with valid access tokens can refresh
    - Same refresh token is reused (no token rotation)
    - Prevents refresh token abuse
    - Requires proactive token refresh (before expiry)
    """
    try:
        tokens = await auth_service.refresh_access_token(refresh_data.refresh_token)
        if not tokens:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            user=tokens["user"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")

@router.post("/logout-all-devices", response_model=dict)
async def logout_all_devices(current_user: dict = Depends(get_current_user)):
    """Logout from all devices by revoking all refresh tokens."""
    success = await auth_service.revoke_all_refresh_tokens(current_user["id"])
    if success:
        return {"message": "Logged out from all devices"}
    else:
        raise HTTPException(status_code=500, detail="Failed to logout from all devices")

@router.get("/token-settings", response_model=dict)
async def get_token_settings():
    """Get current token timing settings."""
    # Calculate refresh token duration in minutes for display
    refresh_minutes = auth_service.refresh_token_expire_days * 24 * 60 if auth_service.refresh_token_expire_days < 1 else auth_service.refresh_token_expire_days * 24 * 60
    
    return {
        "access_token_expire_minutes": auth_service.access_token_expire_minutes,
        "refresh_token_expire_days": auth_service.refresh_token_expire_days,
        "refresh_token_expire_minutes": round(refresh_minutes, 2),
        "cleanup_interval_seconds": 60,  # From config
        "description": {
            "access_token": "Short-lived token for API requests",
            "refresh_token": "Long-lived token for getting new access tokens",
            "production_mode": "Standard durations for production use"
        }
    }

@router.get("/debug-sessions", response_model=dict)
async def debug_sessions():
    """Get debug information about all sessions."""
    return await auth_service.get_all_sessions_info()

@router.post("/cleanup-sessions", response_model=dict)
async def cleanup_sessions():
    """Manually trigger session cleanup."""
    cleaned_count = await auth_service.cleanup_expired_sessions()
    active_count = await auth_service.get_active_sessions_count()
    return {
        "message": f"Cleanup completed",
        "sessions_cleaned": cleaned_count,
        "active_sessions_remaining": active_count
    }



@router.get("/debug-refresh-tokens", response_model=dict, summary="Debug Refresh Tokens")
async def debug_refresh_tokens(current_user: dict = Depends(get_current_user)):
    """
    Debug endpoint to see all refresh tokens for the current user.
    
    **Usage:**
    - Shows all refresh tokens for the authenticated user
    - Includes expiration times and revocation status
    - Useful for monitoring refresh token lifecycle
    """
    try:
        from app.db.repositories import RefreshTokenRepository
        from app.db.database import db_service
        from datetime import datetime, timezone
        
        if not db_service.client:
            return {"error": "Database client not initialized"}
        
        # Get all refresh tokens for the current user
        result = await db_service.client.execute(
            "SELECT id, refresh_token, expires_at, is_revoked, created_at FROM refresh_tokens WHERE user_id = ?",
            [current_user["id"]]
        )
        
        tokens = []
        current_time = datetime.now(timezone.utc)
        
        for row in result.rows:
            token_id, refresh_token, expires_at_str, is_revoked, created_at = row
            
            try:
                # Parse expiration timestamp
                if isinstance(expires_at_str, str):
                    if 'T' in expires_at_str:
                        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                    else:
                        expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                elif isinstance(expires_at_str, (int, float)):
                    if expires_at_str > 1e12:  # Likely milliseconds
                        expires_at = datetime.fromtimestamp(expires_at_str / 1000, tz=timezone.utc)
                    else:  # Likely seconds
                        expires_at = datetime.fromtimestamp(expires_at_str, tz=timezone.utc)
                elif isinstance(expires_at_str, datetime):
                    expires_at = expires_at_str
                else:
                    expires_at = None
                
                time_remaining = (expires_at - current_time).total_seconds() if expires_at else None
                is_expired = time_remaining <= 0 if time_remaining is not None else None
                
                tokens.append({
                    "token_id": token_id,
                    "token_preview": refresh_token[:20] + "..." if len(refresh_token) > 20 else refresh_token,
                    "expires_at": str(expires_at_str),
                    "time_remaining_seconds": max(0, int(time_remaining)) if time_remaining is not None else None,
                    "is_expired": is_expired,
                    "is_revoked": bool(is_revoked),
                    "created_at": str(created_at),
                    "status": "expired" if is_expired else ("revoked" if is_revoked else "active")
                })
                
            except Exception as e:
                tokens.append({
                    "token_id": token_id,
                    "error": f"Error parsing token: {e}",
                    "status": "error"
                })
        
        return {
            "user_id": current_user["id"],
            "username": current_user["username"],
            "current_time": current_time.isoformat(),
            "total_refresh_tokens": len(tokens),
            "active_tokens": len([t for t in tokens if t.get("status") == "active"]),
            "expired_tokens": len([t for t in tokens if t.get("status") == "expired"]),
            "revoked_tokens": len([t for t in tokens if t.get("status") == "revoked"]),
            "tokens": tokens
        }
        
    except Exception as e:
        return {"error": f"Error getting refresh tokens: {str(e)}"}

 

 