from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/settings")
 
@router.get("/profile", tags=["Settings"])
async def user_profile(current_user: dict = Depends(get_current_user)):
    return JSONResponse({"user": current_user}) 