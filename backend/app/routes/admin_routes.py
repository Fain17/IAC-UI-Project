from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.services.user_management_service import (
    get_all_users, get_user_by_id, create_admin_user, 
    delete_admin_user, update_user_active_status, get_user_permissions, 
    get_user_groups, assign_user_to_group, remove_user_from_group, update_user_permissions,
    get_all_user_permissions, create_user_group, get_all_user_groups, delete_user_group, update_user_group
)
from app.auth.dependencies import get_current_admin_user, get_current_user
from app.db.models import AdminUserCreate, AdminUserPermissionUpdate, UserGroupCreate, UserGroupUpdate, UserRole
from typing import List, Optional
import logging
from app.db.repositories import WorkflowRepository
from datetime import datetime
from app.db.repositories import UserRepository, UserPermissionRepository
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Pydantic models for role permission management
class RolePermissionAdd(BaseModel):
    role: str  # admin, manager, viewer
    permission: str  # read, write, delete, execute
    resource_type: str  # workflow, user, group, system, etc.

class RolePermissionRemove(BaseModel):
    role: str  # admin, manager, viewer
    permission: str  # read, write, delete, execute
    resource_type: str  # workflow, user, group, system, etc.

class RolePermissionResponse(BaseModel):
    role: str
    permission: str
    resource_type: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

async def has_admin_role(user_id: str) -> bool:
    """
    Check if a user has admin role in permissions.
    This covers both permanent admins (is_admin=true) and temporary admins (role=admin, is_admin=false).
    """
    try:
        permissions = await get_user_permissions(user_id)
        return permissions and permissions.get("role") == UserRole.ADMIN
    except Exception as e:
        logger.error(f"Error checking admin role for user {user_id}: {e}")
        return False

async def check_user_permission(user_id: str, permission: str, resource_type: str) -> bool:
    """
    Check if a user has a specific permission on a resource type.
    This checks the user's role and then checks if that role has the required permission.
    """
    try:
        # Get user's role
        permissions = await get_user_permissions(user_id)
        if not permissions:
            return False
        
        user_role = permissions.get("role")
        if not user_role:
            return False
        
        # Admin role has all permissions
        if user_role == UserRole.ADMIN:
            return True
        
        # Check if the role has the specific permission
        from app.db.repositories import RolePermissionRepository
        return await RolePermissionRepository.has_permission(user_role, permission, resource_type)
        
    except Exception as e:
        logger.error(f"Error checking permission {permission} for user {user_id} on resource {resource_type}: {e}")
        return False

router = APIRouter(prefix="/admin")

# Admin Routes - Access Control
# All routes in this router require admin role in permissions (either permanent or temporary admin)
# - Permanent admins: is_admin=true in database, cannot be downgraded
# - Temporary admins: role=admin in permissions but is_admin=false, can be downgraded
# - Regular users: role=manager/viewer, cannot access admin routes

# User Management Endpoints
@router.get("/users", tags=["Admin Users"])
async def get_all_users_route(
    role: str = None,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get all users (admin only).
    Returns a list of all users in the system.
    
    Query parameters:
    - role: Filter users by role (admin, manager, viewer)
    """
    users = await get_all_users()
    
    # Filter by role if specified
    if role:
        if role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER]:
            raise HTTPException(status_code=400, detail="Invalid role. Must be admin, manager, or viewer")
        
        filtered_users = []
        for user in users:
            permissions = await get_user_permissions(user["id"])
            user_role = permissions["role"] if permissions else UserRole.VIEWER
            if user_role == role:
                filtered_users.append(user)
        users = filtered_users
    
    return JSONResponse({
        "users": users,
        "count": len(users),
        "filtered_by": role if role else "all"
    })

@router.get("/users/{user_id}", tags=["Admin Users"])
async def get_user_route(
    user_id: str,
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
        "role": permissions["role"] if permissions else UserRole.VIEWER,
        "groups": groups
    }
    
    return JSONResponse(user_data)

@router.post("/users", tags=["Admin Users"])
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
        "role": "manager",
        "group_id": 1
    }
    """
    result = await create_admin_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        role=user_data.role,
        group_id=user_data.group_id
    )
    
    if result["success"]:
        return JSONResponse(result, status_code=201)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@router.put("/users/{user_id}/permissions", tags=["Admin User Permissions"])
async def update_user_permissions_route(
    user_id: str,
    permission_data: AdminUserPermissionUpdate,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Update user permissions (admin only).
    
    Example request body:
    {
        "role": "manager",
        "is_active": true
    }
    
    Roles:
    - admin: Full access to all features
    - manager: Can read, write, and execute workflows, manage users and groups
    - viewer: Can only read and execute workflows
    """
    try:
        # Validate role if provided
        if permission_data.role:
            if permission_data.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER]:
                raise HTTPException(status_code=400, detail="Invalid role. Must be admin, manager, or viewer")
            
            # Prevent admin from downgrading themselves
            if user_id == current_user["id"] and permission_data.role and permission_data.role != UserRole.ADMIN:
                raise HTTPException(status_code=400, detail="Cannot downgrade your own admin privileges")
            
            # Prevent downgrading permanent admins (is_admin=true)
            if permission_data.role and permission_data.role != UserRole.ADMIN:
                target_user = await get_user_by_id(user_id)
                if target_user and target_user.get("is_admin", False):
                    raise HTTPException(
                        status_code=400, 
                        detail="Cannot downgrade permanent admin users. These users have permanent admin privileges (is_admin=true) that cannot be revoked."
                    )
        
        # Update user permissions
        if permission_data.role:
            result = await update_user_permissions(user_id, permission_data.role, current_admin_id=current_user["id"])
            if not result.get("success", False):
                raise HTTPException(status_code=400, detail=result.get("error", "Failed to update user permissions"))
        
        # Update user active status if provided
        if permission_data.is_active is not None:
            result = await update_user_active_status(user_id, permission_data.is_active)
            if not result:
                raise HTTPException(status_code=400, detail="Failed to update user active status")
        
        # Get target user info to determine admin status
        target_user = await get_user_by_id(user_id)

        return JSONResponse({
            "success": True,
            "message": "User permissions updated successfully",
            "user_id": user_id,
            "updated_data": permission_data.model_dump(exclude_unset=True),
            "admin_info": {
                "is_permanent_admin": target_user.get("is_admin", False) if 'target_user' in locals() else None,
                "admin_type": "permanent" if 'target_user' in locals() and target_user.get("is_admin", False) else "temporary",
                "can_be_downgraded": 'target_user' in locals() and not target_user.get("is_admin", False)
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user permissions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/users/{user_id}/elevate-admin", tags=["Admin User Permissions"])
async def elevate_user_to_admin_route(
    user_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Temporarily elevate a user to admin role (admin only).
    This is a temporary elevation that can be revoked.
    
    Security Rules:
    - Only existing admins can elevate users to admin
    - Admin users cannot be elevated (they're already admin)
    - This creates a temporary admin elevation
    """
    try:
        # Prevent admin from elevating themselves
        if user_id == current_user["id"]:
            raise HTTPException(status_code=400, detail="Cannot elevate your own admin privileges")
        
        # Get target user info
        target_user = await get_user_by_id(user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user is already admin
        if target_user.get("is_admin", False):
            raise HTTPException(status_code=400, detail="User is already an admin")
        
        # Elevate user to admin
        result = await update_user_permissions(
            user_id, 
            role=UserRole.ADMIN, 
            current_admin_id=current_user["id"]
        )
        
        if result.get("success", False):
            return JSONResponse({
                "success": True,
                "message": f"User '{target_user['username']}' has been elevated to temporary admin role",
                "user_id": user_id,
                "elevated_at": datetime.now().isoformat(),
                "elevated_by": current_user["id"],
                "admin_type": "temporary",
                "note": "This user now has admin role but their is_admin column remains false. They can be downgraded later since they are a temporary admin."
            })
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to elevate user to admin"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error elevating user to admin: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/users/{user_id}/revoke-admin", tags=["Admin User Permissions"])
async def revoke_admin_privileges_route(
    user_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Revoke admin privileges from a user (admin only).
    This can only be done by other admins.
    
    Security Rules:
    - Only admins can revoke admin privileges
    - Admin users cannot revoke their own privileges
    - This downgrades the user to viewer role
    """
    try:
        # Prevent admin from revoking their own privileges
        if user_id == current_user["id"]:
            raise HTTPException(status_code=400, detail="Cannot revoke your own admin privileges")
        
        # Get target user info
        target_user = await get_user_by_id(user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user is actually an admin
        if not target_user.get("is_admin", False):
            raise HTTPException(status_code=400, detail="User is not an admin")
        
        # Revoke admin privileges (downgrade to viewer)
        result = await update_user_permissions(
            user_id, 
            role=UserRole.VIEWER, 
            current_admin_id=current_user["id"]
        )
        
        if result.get("success", False):
            return JSONResponse({
                "success": True,
                "message": f"Temporary admin privileges revoked from user '{target_user['username']}'",
                "user_id": user_id,
                "revoked_at": datetime.now().isoformat(),
                "revoked_by": current_user["id"],
                "new_role": "viewer",
                "note": "This user was a temporary admin (role=admin, is_admin=false). Their admin privileges have been revoked and they are now a viewer."
            })
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to revoke admin privileges"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking admin privileges: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/users/{user_id}", tags=["Admin Users"])
async def delete_user_route(
    user_id: str,
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

@router.patch("/users/{user_id}/active-status", tags=["Admin Users"])
async def update_user_active_status_route(
    user_id: str,
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

@router.get("/users/permissions/all", tags=["Admin User Permissions"])
async def get_all_user_permissions_route(
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get all user permissions (admin only).
    Returns a list of all users with their roles and permissions.
    
    Role-based permissions:
    - admin: read, write, execute, delete (full access)
    - manager: read, write, execute (can manage workflows and users)
    - viewer: read, execute (can only view and run workflows)
    """
    try:
        permissions = await get_all_user_permissions()
        
        # Enhance the response with role-based permission details
        enhanced_permissions = []
        for perm in permissions:
            role = perm.get("role", "viewer")
            role_permissions = {
                "admin": ["read", "write", "execute", "delete"],
                "manager": ["read", "write", "execute"],
                "viewer": ["read", "execute"]
            }.get(role, ["read"])
            
            enhanced_permissions.append({
                **perm,
                "role_permissions": role_permissions,
                "description": f"{role.title()} role with {', '.join(role_permissions)} permissions"
            })
        
        return JSONResponse({
            "success": True,
            "permissions": enhanced_permissions,
            "count": len(enhanced_permissions),
            "role_summary": {
                "admin": len([p for p in enhanced_permissions if p["role"] == "admin"]),
                "manager": len([p for p in enhanced_permissions if p["role"] == "manager"]),
                "viewer": len([p for p in enhanced_permissions if p["role"] == "viewer"])
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting all user permissions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/users/{user_id}/permissions", tags=["Admin User Permissions"])
async def get_user_permissions_route(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get permissions for a specific user.
    Returns the user's role and associated permissions.
    
    Role-based permissions:
    - admin: read, write, execute, delete (full access)
    - manager: read, write, execute (can manage workflows and users)
    - viewer: read, execute (can only view and run workflows)
    """
    try:
        permissions = await get_user_permissions(user_id)
        
        if not permissions:
            return JSONResponse({
                "success": True,
                "user_id": user_id,
                "role": "viewer",
                "permissions": ["read", "execute"],
                "description": "Default viewer role with read and execute permissions"
            })
        
        role = permissions.get("role", "viewer")
        role_permissions = {
            "admin": ["read", "write", "execute", "delete"],
            "manager": ["read", "write", "execute"],
            "viewer": ["read", "execute"]
        }.get(role, ["read"])
        
        return JSONResponse({
            "success": True,
            "user_id": user_id,
            "role": role,
            "permissions": role_permissions,
            "description": f"{role.title()} role with {', '.join(role_permissions)} permissions",
            "created_at": permissions.get("created_at"),
            "updated_at": permissions.get("updated_at")
        })
        
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/users/{user_id}/groups", tags=["Admin User Groups"])
async def get_user_groups_route(
    user_id: str,
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

@router.post("/users/{user_id}/groups/{group_id}", tags=["Admin User Groups"])
async def assign_user_to_group_route(
    user_id: str,
    group_id: str,
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

@router.delete("/users/{user_id}/groups/{group_id}", tags=["Admin User Groups"])
async def remove_user_from_group_route(
    user_id: str,
    group_id: str,
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


# User Statistics
@router.get("/users/stats", tags=["Admin Users"])
async def get_user_stats_route(current_user: dict = Depends(get_current_admin_user)):
    """
    Get user statistics (admin only).
    Returns counts of active/inactive users and permission levels.
    """
    users = await get_all_users()
    
    total_users = len(users)
    active_users = sum(1 for user in users if user["is_active"])
    inactive_users = total_users - active_users
    
    # Count admin users based on role (both permanent and temporary)
    admin_users_count = 0
    for user in users:
        if await has_admin_role(user["id"]):
            admin_users_count += 1
    
    # Get permission statistics
    permission_stats = {}
    for user in users:
        permissions = await get_user_permissions(user["id"])
        role = permissions["role"] if permissions else "viewer"
        permission_stats[role] = permission_stats.get(role, 0) + 1
    
    return JSONResponse({
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "admin_users": admin_users_count,
        "permission_distribution": permission_stats
    })

# Group Management Endpoints
@router.post("/groups", tags=["Admin User Groups"])
async def create_group_route(
    group_data: UserGroupCreate,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Create a new user group (admin only).
    
    Example request body:
    {
        "name": "Developers",
        "description": "Development team members"
    }
    """
    result = await create_user_group(
        name=group_data.name,
        description=group_data.description
    )
    
    if result["success"]:
        return JSONResponse(result, status_code=201)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@router.get("/groups", tags=["Admin User Groups"])
async def get_all_groups_route(
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get all user groups (admin only).
    Returns a list of all groups in the system.
    """
    groups = await get_all_user_groups()
    return JSONResponse({
        "groups": groups,
        "count": len(groups)
    })

@router.get("/groups/{group_id}", tags=["Admin User Groups"])
async def get_group_route(
    group_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get a specific user group by ID (admin only).
    Returns detailed group information.
    """
    try:
        from app.db.repositories import UserGroupRepository
        group = await UserGroupRepository.get_by_id(group_id)
        
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Get users in this group
        from app.services.user_management_service import get_group_users
        users = await get_group_users(group_id)
        
        group_data = {
            **group,
            "users": users,
            "user_count": len(users)
        }
        
        return JSONResponse({
            "success": True,
            "group": group_data
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 

@router.get("/groups/{group_id}/workflows", tags=["Admin"])
async def get_group_workflows_route(
    group_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    List workflows created by members of the specified group (admin only).
    """
    try:
        workflows = await WorkflowRepository.get_all_by_user_groups(user_id=0, group_id=group_id)
        return JSONResponse({
            "success": True,
            "group_id": group_id,
            "workflows": workflows,
            "count": len(workflows)
        })
    except Exception as e:
        logger.error(f"Error listing workflows for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 

@router.get("/groups/{group_id}/users", tags=["Admin User Groups"])
async def get_group_users_list_route(
    group_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get all users present in a specific group (admin only).
    Returns a list of users assigned to the specified group.
    """
    try:
        from app.services.user_management_service import get_group_users
        users = await get_group_users(group_id)
        
        return JSONResponse({
            "success": True,
            "group_id": group_id,
            "users": users,
            "count": len(users)
        })
    except Exception as e:
        logger.error(f"Error getting users for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/groups/{group_id}", tags=["Admin User Groups"])
async def delete_group_route(
    group_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Delete a user group (admin only).
    This will also remove all user assignments and workflow shares for this group.
    """
    try:
        result = await delete_user_group(group_id)
        
        if result["success"]:
            return JSONResponse(result)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/groups/{group_id}", tags=["Admin User Groups"])
async def update_group_route(
    group_id: str,
    group_data: UserGroupUpdate,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Update a user group (admin only).
    Updates the name and/or description of an existing group.
    
    Example request body:
    {
        "name": "New Group Name",
        "description": "Updated group description"
    }
    
    Both fields are optional - only provided fields will be updated.
    """
    try:
        result = await update_user_group(
            group_id=group_id,
            name=group_data.name,
            description=group_data.description
        )
        
        if result["success"]:
            return JSONResponse(result)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/workflows", tags=["Admin Workflows"])
async def get_all_workflows_route(
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get all workflows in the system (admin only).
    Returns all workflows regardless of ownership or team membership.
    """
    try:
        # Get all workflows from all users
        all_workflows = []
        
        # Get all users first
        users = await get_all_users()
        
        for user in users:
            user_workflows = await WorkflowRepository.get_all_by_user(user["id"])
            all_workflows.extend(user_workflows)
        
        # Sort by creation date (newest first)
        all_workflows.sort(key=lambda w: w.get("created_at", ""), reverse=True)
        
        return JSONResponse({
            "success": True,
            "workflows": all_workflows,
            "count": len(all_workflows),
            "total_users": len(users)
        })
    except Exception as e:
        logger.error(f"Error getting all workflows: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 

@router.get("/admin-users", tags=["Admin User Permissions"])
async def get_admin_users_route(
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get list of all admin users (admin only).
    Shows which users have admin privileges and their current status.
    """
    try:
        # Get all users
        users = await get_all_users()
        
        # Filter admin users
        admin_users = []
        for user in users:
            # Check if user has admin role (either permanent or temporary)
            if await has_admin_role(user["id"]):
                # Get their current permissions
                permissions = await get_user_permissions(user["id"])
                role = permissions.get("role", "admin") if permissions else "admin"
                
                # Determine if they are permanent or temporary admin
                is_permanent_admin = user.get("is_admin", False)
                admin_type = "permanent" if is_permanent_admin else "temporary"
                
                admin_users.append({
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "role": role,
                    "is_active": user.get("is_active", True),
                    "admin_type": admin_type,
                    "created_at": user.get("created_at"),
                    "updated_at": user.get("updated_at")
                })
        
        return JSONResponse({
            "success": True,
            "admin_users": admin_users,
            "count": len(admin_users),
            "note": "Permanent admins (is_admin=true) cannot be downgraded. Temporary admins (role=admin, is_admin=false) can be revoked."
        })
        
    except Exception as e:
        logger.error(f"Error getting admin users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 

@router.get("/users/{user_id}/admin-status", tags=["Admin User Permissions"])
async def get_user_admin_status_route(
    user_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get the admin status of a specific user (admin only).
    Shows whether the user is a permanent admin (is_admin=true) or temporary admin (role=admin, is_admin=false).
    """
    try:
        # Get target user info
        target_user = await get_user_by_id(user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user permissions
        permissions = await get_user_permissions(user_id)
        role = permissions.get("role", "viewer") if permissions else "viewer"
        
        # Determine admin status
        is_permanent_admin = target_user.get("is_admin", False)
        is_temporary_admin = (role == UserRole.ADMIN and not is_permanent_admin)
        
        admin_status = {
            "user_id": user_id,
            "username": target_user["username"],
            "email": target_user["email"],
            "current_role": role,
            "is_permanent_admin": is_permanent_admin,
            "is_temporary_admin": is_temporary_admin,
            "can_be_downgraded": is_temporary_admin,  # Only temporary admins can be downgraded
            "admin_type": "permanent" if is_permanent_admin else ("temporary" if is_temporary_admin else "none"),
            "note": "Permanent admins (is_admin=true) cannot be downgraded. Temporary admins (role=admin, is_admin=false) can be revoked."
        }
        
        return JSONResponse({
            "success": True,
            "admin_status": admin_status
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user admin status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 

@router.post("/users/{user_id}/promote-permanent-admin", tags=["Admin User Permissions"])
async def promote_to_permanent_admin_route(
    user_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Promote a user to permanent admin (admin only).
    This sets their is_admin column to true, making them a permanent admin who cannot be downgraded.
    
    WARNING: This is a permanent change that cannot be undone easily.
    Only use this for users who should have permanent admin privileges.
    """
    try:
        # Prevent admin from promoting themselves
        if user_id == current_user["id"]:
            raise HTTPException(status_code=400, detail="Cannot promote yourself to permanent admin")
        
        # Get target user info
        target_user = await get_user_by_id(user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user is already a permanent admin
        if target_user.get("is_admin", False):
            raise HTTPException(status_code=400, detail="User is already a permanent admin")
        
        # Check if user has admin role in permissions
        permissions = await get_user_permissions(user_id)
        if not permissions or permissions.get("role") != UserRole.ADMIN:
            raise HTTPException(status_code=400, detail="User must have admin role before being promoted to permanent admin")
        
        # Promote to permanent admin by updating is_admin column
        success = await UserRepository.update_is_admin(user_id, True)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to promote user to permanent admin")
        
        return JSONResponse({
            "success": True,
            "message": f"User '{target_user['username']}' has been promoted to permanent admin",
            "user_id": user_id,
            "promoted_at": datetime.now().isoformat(),
            "promoted_by": current_user["id"],
            "admin_type": "permanent",
            "warning": "This user is now a permanent admin (is_admin=true) and cannot be downgraded. This change is permanent."
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error promoting user to permanent admin: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 

@router.get("/test-admin-access", tags=["Admin User Permissions"])
async def test_admin_access_route(
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Test route to verify admin access (admin only).
    This route helps verify that the role-based admin access control is working correctly.
    """
    try:
        # Get user permissions to show current role
        permissions = await get_user_permissions(current_user["id"])
        current_role = permissions.get("role", "none") if permissions else "none"
        
        # Check if user has admin role
        has_admin = await has_admin_role(current_user["id"])
        
        return JSONResponse({
            "success": True,
            "message": "Admin access verified successfully",
            "user_info": {
                "id": current_user["id"],
                "username": current_user["username"],
                "email": current_user["email"],
                "is_admin_column": current_user.get("is_admin", False),
                "current_role": current_role,
                "has_admin_role": has_admin,
                "admin_type": "permanent" if current_user.get("is_admin", False) else ("temporary" if has_admin else "none")
            },
            "note": "This route verifies that role-based admin access control is working correctly."
        })
        
    except Exception as e:
        logger.error(f"Error testing admin access: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 

# Role Permission Management Endpoints
# 
# This system provides granular control over what each role can do:
# 
# ROLES:
# - admin: Has all permissions by default (cannot be modified - always has read, write, delete, execute)
# - manager: Can read/write/execute workflows, read users, read/write groups, read system
# - viewer: Can only read workflows, users, groups, and system
# 
# PERMISSIONS:
# - read: View/list resources
# - write: Create/update resources  
# - delete: Remove resources
# - execute: Run/perform actions on resources
# 
# RESOURCE TYPES:
# - workflow: Workflow management operations
# - user: User management operations
# - group: Group management operations
# - system: System-level operations
# 
# IMPORTANT: Admin role permissions are immutable and always include all permissions on all resources.
# Attempting to modify admin role permissions will result in an error.
# 
# USAGE:
# - GET /admin/role-permissions - View all role permissions
# - GET /admin/role-permissions/{role} - View permissions for specific role
# - POST /admin/role-permissions - Add permission to role (admin role cannot be modified)
# - DELETE /admin/role-permissions - Remove permission from role (admin role cannot be modified)
# - POST /admin/role-permissions/reset/{role} - Reset role to defaults (admin role cannot be reset)
#
@router.get("/role-permissions", tags=["Admin Role Permissions"])
async def get_all_role_permissions_route(
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get all role permissions (admin only).
    Returns a comprehensive list of all permissions for all roles in grouped format.
    """
    try:
        from app.db.repositories import RolePermissionRepository
        
        permissions = await RolePermissionRepository.get_all()
        
        # Group permissions by role and resource type for better organization
        grouped_permissions = []
        role_resource_map = {}
        
        for perm in permissions:
            role = perm["role"]
            resource_type = perm["resource_type"]
            
            # Create key for role-resource combination
            key = (role, resource_type)
            
            if key not in role_resource_map:
                role_resource_map[key] = {
                    "role": role,
                    "resource_type": resource_type,
                    "permissions": [],
                    "created_at": perm["created_at"],
                    "updated_at": perm["updated_at"]
                }
            
            # Add permission to the list
            role_resource_map[key]["permissions"].append(perm["permission"])
        
        # Convert to list and sort permissions within each group
        for group in role_resource_map.values():
            group["permissions"].sort()  # Sort permissions alphabetically
            grouped_permissions.append(group)
        
        # Sort by role, then by resource type
        grouped_permissions.sort(key=lambda x: (x["role"], x["resource_type"]))
        
        return JSONResponse({
            "success": True,
            "permissions": grouped_permissions,
            "count": len(grouped_permissions),
            "total_permissions": len(permissions),
            "note": "Permissions are grouped by role and resource type for better readability"
        })
        
    except Exception as e:
        logger.error(f"Error getting role permissions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/role-permissions/{role}", tags=["Admin Role Permissions"])
async def get_role_permissions_route(
    role: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get permissions for a specific role (admin only).
    Returns all permissions associated with the specified role in grouped format.
    """
    try:
        from app.db.repositories import RolePermissionRepository
        
        if role not in ["admin", "manager", "viewer"]:
            raise HTTPException(status_code=400, detail="Invalid role. Must be admin, manager, or viewer")
        
        permissions = await RolePermissionRepository.get_by_role(role)
        
        # Group permissions by resource type
        grouped_permissions = []
        resource_map = {}
        
        for perm in permissions:
            resource_type = perm["resource_type"]
            
            if resource_type not in resource_map:
                resource_map[resource_type] = {
                    "role": role,
                    "resource_type": resource_type,
                    "permissions": [],
                    "created_at": perm["created_at"],
                    "updated_at": perm["updated_at"]
                }
            
            resource_map[resource_type]["permissions"].append(perm["permission"])
        
        # Convert to list and sort permissions within each group
        for group in resource_map.values():
            group["permissions"].sort()  # Sort permissions alphabetically
            grouped_permissions.append(group)
        
        # Sort by resource type
        grouped_permissions.sort(key=lambda x: x["resource_type"])
        
        return JSONResponse({
            "success": True,
            "role": role,
            "permissions": grouped_permissions,
            "count": len(grouped_permissions),
            "total_permissions": len(permissions),
            "note": f"Permissions for {role} role grouped by resource type"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting permissions for role {role}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/role-permissions/{role}/{resource_type}", tags=["Admin Role Permissions"])
async def get_role_resource_permissions_route(
    role: str,
    resource_type: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get permissions for a specific role and resource type (admin only).
    Returns permissions for the specified role on the specified resource type.
    """
    try:
        from app.db.repositories import RolePermissionRepository
        
        if role not in ["admin", "manager", "viewer"]:
            raise HTTPException(status_code=400, detail="Invalid role. Must be admin, manager, or viewer")
        
        permissions = await RolePermissionRepository.get_by_role_and_resource(role, resource_type)
        
        # Extract permission names and sort them
        permission_names = [perm["permission"] for perm in permissions]
        permission_names.sort()
        
        return JSONResponse({
            "success": True,
            "role": role,
            "resource_type": resource_type,
            "permissions": permission_names,
            "detailed_permissions": permissions,
            "count": len(permissions),
            "note": f"Permissions for {role} role on {resource_type} resource"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting permissions for role {role} on resource {resource_type}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/role-permissions", tags=["Admin Role Permissions"])
async def add_role_permission_route(
    permission_data: RolePermissionAdd,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Add a permission to a role (admin only).
    This allows admins to customize what each role can do.
    
    Note: Admin role permissions cannot be modified as they have all permissions by default.
    """
    try:
        from app.db.repositories import RolePermissionRepository
        
        # Validate role
        if permission_data.role not in ["admin", "manager", "viewer"]:
            raise HTTPException(status_code=400, detail="Invalid role. Must be admin, manager, or viewer")
        
        # Validate permission
        if permission_data.permission not in ["read", "write", "delete", "execute"]:
            raise HTTPException(status_code=400, detail="Invalid permission. Must be read, write, delete, or execute")
        
        # Validate resource type
        if permission_data.resource_type not in ["workflow", "user", "group", "system"]:
            raise HTTPException(status_code=400, detail="Invalid resource type. Must be workflow, user, group, or system")
        
        # Prevent modification of admin role permissions
        if permission_data.role == "admin":
            raise HTTPException(
                status_code=400, 
                detail="Cannot modify admin role permissions. Admin role has all permissions by default."
            )
        
        # Check if permission already exists
        if await RolePermissionRepository.has_permission(
            permission_data.role, 
            permission_data.permission, 
            permission_data.resource_type
        ):
            raise HTTPException(
                status_code=400, 
                detail=f"Permission {permission_data.permission} already exists for role {permission_data.role} on resource {permission_data.resource_type}"
            )
        
        # Add the permission
        success = await RolePermissionRepository.add_permission(
            permission_data.role,
            permission_data.permission,
            permission_data.resource_type
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add permission")
        
        return JSONResponse({
            "success": True,
            "message": f"Permission {permission_data.permission} added to role {permission_data.role} for resource {permission_data.resource_type}",
            "permission": {
                "role": permission_data.role,
                "permission": permission_data.permission,
                "resource_type": permission_data.resource_type
            }
        }, status_code=201)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding permission: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/role-permissions", tags=["Admin Role Permissions"])
async def remove_role_permission_route(
    permission_data: RolePermissionRemove,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Remove a permission from a role (admin only).
    This allows admins to restrict what each role can do.
    
    Note: Admin role permissions cannot be modified as they have all permissions by default.
    """
    try:
        from app.db.repositories import RolePermissionRepository
        
        # Validate role
        if permission_data.role not in ["admin", "manager", "viewer"]:
            raise HTTPException(status_code=400, detail="Invalid role. Must be admin, manager, or viewer")
        
        # Validate permission
        if permission_data.permission not in ["read", "write", "delete", "execute"]:
            raise HTTPException(status_code=400, detail="Invalid permission. Must be read, write, delete, or execute")
        
        # Validate resource type
        if permission_data.resource_type not in ["workflow", "user", "group", "system"]:
            raise HTTPException(status_code=400, detail="Invalid resource type. Must be workflow, user, group, or system")
        
        # Prevent modification of admin role permissions
        if permission_data.role == "admin":
            raise HTTPException(
                status_code=400, 
                detail="Cannot modify admin role permissions. Admin role has all permissions by default."
            )
        
        # Check if permission exists
        if not await RolePermissionRepository.has_permission(
            permission_data.role, 
            permission_data.permission, 
            permission_data.resource_type
        ):
            raise HTTPException(
                status_code=400, 
                detail=f"Permission {permission_data.permission} does not exist for role {permission_data.role} on resource {permission_data.resource_type}"
            )
        
        # Remove the permission
        success = await RolePermissionRepository.remove_permission(
            permission_data.role,
            permission_data.permission,
            permission_data.resource_type
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to remove permission")
        
        return JSONResponse({
            "success": True,
            "message": f"Permission {permission_data.permission} removed from role {permission_data.role} for resource {permission_data.resource_type}",
            "removed_permission": {
                "role": permission_data.role,
                "permission": permission_data.permission,
                "resource_type": permission_data.resource_type
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing permission: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/role-permissions/reset/{role}", tags=["Admin Role Permissions"])
async def reset_role_permissions_route(
    role: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Reset a role to its default permissions (admin only).
    This removes all custom permissions and restores the default permissions for the role.
    
    Note: Admin role cannot be reset as it has all permissions by default.
    """
    try:
        from app.db.repositories import RolePermissionRepository
        
        # Validate role
        if role not in ["admin", "manager", "viewer"]:
            raise HTTPException(status_code=400, detail="Invalid role. Must be admin, manager, or viewer")
        
        # Prevent reset of admin role
        if role == "admin":
            raise HTTPException(
                status_code=400, 
                detail="Cannot reset admin role permissions. Admin role has all permissions by default."
            )
        
        # Get current permissions for the role
        current_permissions = await RolePermissionRepository.get_by_role(role)
        
        # Remove all current permissions
        for perm in current_permissions:
            await RolePermissionRepository.remove_permission(
                perm["role"], 
                perm["permission"], 
                perm["resource_type"]
            )
        
        # Re-add default permissions based on role
        default_permissions = []
        if role == "manager":
            default_permissions = [
                ("manager", "read", "workflow"),
                ("manager", "write", "workflow"),
                ("manager", "execute", "workflow"),
                ("manager", "read", "user"),
                ("manager", "read", "group"),
                ("manager", "write", "group"),
                ("manager", "read", "system"),
            ]
        elif role == "viewer":
            default_permissions = [
                ("viewer", "read", "workflow"),
                ("viewer", "read", "user"),
                ("viewer", "read", "group"),
                ("viewer", "read", "system"),
            ]
        
        # Add default permissions back
        for role_name, permission, resource_type in default_permissions:
            await RolePermissionRepository.add_permission(role_name, permission, resource_type)
        
        return JSONResponse({
            "success": True,
            "message": f"Role {role} permissions reset to defaults",
            "role": role,
            "default_permissions": default_permissions,
            "removed_permissions_count": len(current_permissions),
            "added_permissions_count": len(default_permissions)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting role permissions for {role}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 