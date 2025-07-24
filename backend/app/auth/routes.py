import re
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.auth.service import auth_service
from app.auth.dependencies import get_current_user
from typing import Optional

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

class HardResetPasswordRequest(BaseModel):
    email: str
    new_password: str
    confirm_password: str

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
    """Login user and return JWT token."""
    # Determine if input is email or username
    if is_email(user_data.username_or_email):
        user = await auth_service.authenticate_user_by_email(user_data.username_or_email, user_data.password)
    else:
        user = await auth_service.authenticate_user(user_data.username_or_email, user_data.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = auth_service.create_access_token(data={"sub": str(user["id"])})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
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

@router.post("/verify-token")
async def verify_token(request: Request):
    """Verify if a token is valid."""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = auth_header.split(" ")[1]
        payload = await auth_service.verify_token(token)
        
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await auth_service.get_user_by_id(int(user_id))
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {"valid": True, "user": user}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Token verification failed")

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

@router.post("/hard-reset-password", response_model=dict)
async def hard_reset_password(data: HardResetPasswordRequest):
    result = await auth_service.hard_reset_password(
        email=data.email,
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
    from app.db.database import db_service
    if not db_service.client:
        raise HTTPException(status_code=500, detail="Database client not initialized")
    if not username and not email:
        raise HTTPException(status_code=400, detail="Username or email required")
    if username:
        result = await db_service.client.execute(
            "SELECT id FROM users WHERE username = ?",
            [username]
        )
        if result.rows:
            return {"available": False, "field": "username"}
    if email:
        result = await db_service.client.execute(
            "SELECT id FROM users WHERE email = ?",
            [email]
        )
        if result.rows:
            return {"available": False, "field": "email"}
    return {"available": True} 