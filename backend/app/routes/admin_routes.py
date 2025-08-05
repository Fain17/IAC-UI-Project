from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.services.user_management_service import (
    get_all_users, get_user_by_id, create_admin_user, 
    delete_admin_user, update_user_active_status, get_user_permissions, 
    get_user_groups, assign_user_to_group, remove_user_from_group, update_user_permissions
)
from app.auth.dependencies import get_current_admin_user
from app.db.models import AdminUserCreate, AdminUserPermissionUpdate
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

# User Management Endpoints
@router.get("/users", tags=["Admin"])
async def get_all_users_route(
    permission_level: str = None,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get all users (admin only).
    Returns a list of all users in the system.
    
    Query parameters:
    - permission_level: Filter users by permission level (admin, manager, viewer)
    """
    users = await get_all_users()
    
    # Filter by permission level if specified
    if permission_level:
        if permission_level not in ["admin", "manager", "viewer"]:
            raise HTTPException(status_code=400, detail="Invalid permission level. Must be admin, manager, or viewer")
        
        filtered_users = []
        for user in users:
            permissions = await get_user_permissions(user["id"])
            user_permission = permissions["permission_level"] if permissions else "viewer"
            if user_permission == permission_level:
                filtered_users.append(user)
        users = filtered_users
    
    return JSONResponse({
        "users": users,
        "count": len(users),
        "filtered_by": permission_level if permission_level else "all"
    })

@router.get("/users/{user_id}", tags=["Admin"])
async def get_user_route(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get a specific user by ID (admin only).
    Returns detailed user information.
    """
    user = await get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user permissions
    permissions = await get_user_permissions(user_id)
    
    # Get user groups
    groups = await get_user_groups(user_id)
    
    user_data = {
        **user,
        "permission_level": permissions["permission_level"] if permissions else "viewer",
        "groups": groups
    }
    
    return JSONResponse(user_data)

@router.post("/users", tags=["Admin"])
async def create_user_route(
    user_data: AdminUserCreate,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Create a new user (admin only).
    
    Example request body:
    {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "securepassword123",
        "permission_level": "manager",
        "group_id": 1
    }
    """
    result = await create_admin_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        permission_level=user_data.permission_level,
        group_id=user_data.group_id
    )
    
    if result["success"]:
        return JSONResponse(result, status_code=201)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@router.put("/users/{user_id}/permissions", tags=["Admin"])
async def update_user_permissions_route(
    user_id: int,
    permission_data: AdminUserPermissionUpdate,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Update user permissions and active status only (admin only).
    
    Example request body (both fields optional):
    {
        "permission_level": "manager",
        "is_active": false
    }
    """
    # Prevent admin from deactivating themselves
    if user_id == current_user["id"] and permission_data.is_active is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    result = await update_user_permissions(
        user_id=user_id,
        permission_level=permission_data.permission_level,
        is_active=permission_data.is_active
    )
    
    if result["success"]:
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@router.delete("/users/{user_id}", tags=["Admin"])
async def delete_user_route(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Delete a user (admin only).
    This will permanently delete the user and all associated data.
    """
    # Prevent admin from deleting themselves
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    result = await delete_admin_user(user_id)
    
    if result["success"]:
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@router.patch("/users/{user_id}/active-status", tags=["Admin"])
async def update_user_active_status_route(
    user_id: int,
    status_data: AdminUserPermissionUpdate,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Update user's active status (admin only).
    
    Example request body:
    {
        "is_active": false
    }
    """
    # Prevent admin from deactivating themselves
    if user_id == current_user["id"] and status_data.is_active is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    result = await update_user_active_status(user_id, status_data.is_active)
    
    if result["success"]:
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@router.get("/users/{user_id}/permissions", tags=["Admin"])
async def get_user_permissions_route(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get user permissions (admin only).
    Returns the user's permission level.
    """
    permissions = await get_user_permissions(user_id)
    
    if not permissions:
        raise HTTPException(status_code=404, detail="User permissions not found")
    
    return JSONResponse(permissions)

@router.get("/users/{user_id}/groups", tags=["Admin"])
async def get_user_groups_route(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get user's group assignments (admin only).
    Returns a list of groups the user belongs to.
    """
    groups = await get_user_groups(user_id)
    return JSONResponse({
        "user_id": user_id,
        "groups": groups,
        "count": len(groups)
    })

@router.post("/users/{user_id}/groups/{group_id}", tags=["Admin"])
async def assign_user_to_group_route(
    user_id: int,
    group_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Assign a user to a group (admin only).
    """
    result = await assign_user_to_group(user_id, group_id)
    
    if result["success"]:
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@router.delete("/users/{user_id}/groups/{group_id}", tags=["Admin"])
async def remove_user_from_group_route(
    user_id: int,
    group_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Remove a user from a group (admin only).
    """
    result = await remove_user_from_group(user_id, group_id)
    
    if result["success"]:
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

# Bulk Operations
@router.post("/users/bulk-activate", tags=["Admin"])
async def bulk_activate_users_route(
    user_ids: List[int],
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Activate multiple users at once (admin only).
    
    Example request body:
    {
        "user_ids": [1, 2, 3, 4]
    }
    """
    results = []
    success_count = 0
    
    for user_id in user_ids:
        # Prevent admin from affecting themselves
        if user_id == current_user["id"]:
            results.append({
                "user_id": user_id,
                "success": False,
                "error": "Cannot modify your own account"
            })
            continue
        
        result = await update_user_active_status(user_id, True)
        results.append({
            "user_id": user_id,
            **result
        })
        
        if result["success"]:
            success_count += 1
    
    return JSONResponse({
        "total_users": len(user_ids),
        "successful_activations": success_count,
        "failed_activations": len(user_ids) - success_count,
        "results": results
    })

@router.post("/users/bulk-deactivate", tags=["Admin"])
async def bulk_deactivate_users_route(
    user_ids: List[int],
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Deactivate multiple users at once (admin only).
    
    Example request body:
    {
        "user_ids": [1, 2, 3, 4]
    }
    """
    results = []
    success_count = 0
    
    for user_id in user_ids:
        # Prevent admin from affecting themselves
        if user_id == current_user["id"]:
            results.append({
                "user_id": user_id,
                "success": False,
                "error": "Cannot modify your own account"
            })
            continue
        
        result = await update_user_active_status(user_id, False)
        results.append({
            "user_id": user_id,
            **result
        })
        
        if result["success"]:
            success_count += 1
    
    return JSONResponse({
        "total_users": len(user_ids),
        "successful_deactivations": success_count,
        "failed_deactivations": len(user_ids) - success_count,
        "results": results
    })

# User Statistics
@router.get("/users/stats", tags=["Admin"])
async def get_user_stats_route(current_user: dict = Depends(get_current_admin_user)):
    """
    Get user statistics (admin only).
    Returns counts of active/inactive users and permission levels.
    """
    users = await get_all_users()
    
    total_users = len(users)
    active_users = sum(1 for user in users if user["is_active"])
    inactive_users = total_users - active_users
    admin_users = sum(1 for user in users if user["is_admin"])
    
    # Get permission statistics
    permission_stats = {}
    for user in users:
        permissions = await get_user_permissions(user["id"])
        permission_level = permissions["permission_level"] if permissions else "viewer"
        permission_stats[permission_level] = permission_stats.get(permission_level, 0) + 1
    
    return JSONResponse({
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "admin_users": admin_users,
        "permission_distribution": permission_stats
    }) 