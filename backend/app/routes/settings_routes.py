from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.auth.dependencies import get_current_user
from app.services.user_management_service import get_user_permissions

router = APIRouter(prefix="/settings")
 
@router.get("/profile", tags=["Settings"])
async def user_profile(current_user: dict = Depends(get_current_user)):
    return JSONResponse({"user": current_user})

@router.get("/permissions", tags=["Settings"])
async def user_permissions(current_user: dict = Depends(get_current_user)):
    """
    Get current user's permissions.
    Returns the user's permission level and related information.
    """
    permissions = await get_user_permissions(current_user["id"])
    
    if not permissions:
        # Return default viewer permission if no permission record exists
        return JSONResponse({
            "user_id": current_user["id"],
            "permission_level": "viewer",
            "created_at": None,
            "updated_at": None
        })
    
    return JSONResponse(permissions) 