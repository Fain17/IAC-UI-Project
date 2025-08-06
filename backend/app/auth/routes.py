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
import logging

logger = logging.getLogger(__name__)

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
    password: Optional[str] = None

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
    
    # Check if user is inactive
    if isinstance(user, dict) and user.get("error") == "inactive_user":
        raise HTTPException(status_code=401, detail="Account is inactive - please contact an administrator")
    
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



@router.get("/verify-token", tags=["Authentication"])
async def verify_token_route(
    current_user: dict = Depends(get_current_user)
):
    """
    Verify current token validity and get expiry information.
    Returns smart expiry data for frontend optimization.
    """
    try:
        # Get current token from request
        from fastapi import Request
        request = Request
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = auth_header.split(" ")[1]
        
        # Verify token and get session info
        session_info = await auth_service.get_session_info_for_token(token)
        
        if not session_info:
            return JSONResponse({
                "valid": False,
                "error": "Token not found or invalid",
                "should_refresh": False,
                "time_remaining_seconds": 0
            })
        
        time_remaining = session_info["time_remaining_seconds"]
        
        # Determine if refresh is needed (30 seconds threshold)
        should_refresh = time_remaining <= 30
        
        return JSONResponse({
            "valid": True,
            "user": current_user,
            "expires_at": session_info["expires_at"],
            "time_remaining_seconds": time_remaining,
            "should_refresh": should_refresh,
            "refresh_threshold_seconds": 30
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return JSONResponse({
            "valid": False,
            "error": "Token verification failed",
            "should_refresh": False,
            "time_remaining_seconds": 0
        })

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
    # Check if user is admin
    is_admin = current_user.get("is_admin", False)
    
    # For admin users, password is required
    if is_admin:
        if not data.password:
            raise HTTPException(status_code=400, detail="Password is required for admin users")
        result = await auth_service.delete_user_account(user_id=current_user["id"], password=data.password, require_password=True)
    else:
        # For regular users, password is optional
        result = await auth_service.delete_user_account(user_id=current_user["id"], password=data.password or "", require_password=False)
    
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
    """
    Check if this is the first user in the system.
    Used by frontend to determine if the first user should be made admin by default.
    """
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





