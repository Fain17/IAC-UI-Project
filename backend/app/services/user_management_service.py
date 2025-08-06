from app.db.repositories import UserRepository, UserGroupRepository, UserPermissionRepository, UserGroupAssignmentRepository
from app.auth.service import auth_service
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

async def get_all_users() -> List[Dict]:
    """
    Get all users (admin only).
    Returns list of user dictionaries.
    """
    try:
        users = await UserRepository.get_all()
        return users
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []

async def get_user_by_id(user_id: int) -> Optional[Dict]:
    """
    Get a specific user by ID (admin only).
    Returns user dict or None if not found.
    """
    try:
        user = await UserRepository.get_by_id(user_id)
        return user
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        return None

async def create_admin_user(username: str, email: str, password: str, permission_level: str = "viewer", group_id: Optional[int] = None) -> Dict:
    """
    Create a new user with admin privileges (admin only).
    Returns dict with success status and user ID or error message.
    """
    try:
        if not username or not username.strip():
            return {"success": False, "error": "Username is required"}
        
        if not email or not email.strip():
            return {"success": False, "error": "Email is required"}
        
        if not password or len(password) < 6:
            return {"success": False, "error": "Password must be at least 6 characters"}
        
        # Validate permission level
        if permission_level not in ["admin", "manager", "viewer"]:
            return {"success": False, "error": "Invalid permission level. Must be admin, manager, or viewer"}
        
        # Check if username or email already exists
        existing_user = await UserRepository.get_by_username(username)
        if existing_user:
            return {"success": False, "error": "Username already exists"}
        
        existing_email = await UserRepository.get_by_email(email)
        if existing_email:
            return {"success": False, "error": "Email already exists"}
        
        # Hash password
        hashed_password = auth_service.get_password_hash(password)
        
        # Create user (not admin by default)
        success = await UserRepository.create(username.strip(), email.strip(), hashed_password, is_admin=False)
        
        if not success:
            return {"success": False, "error": "Failed to create user"}
        
        # Get the created user's ID
        user = await UserRepository.get_by_username(username)
        if not user:
            return {"success": False, "error": "Failed to retrieve created user"}
        
        user_id = user["id"]
        
        # Create permission record
        permission_success = await UserPermissionRepository.create(user_id, permission_level)
        if not permission_success:
            # Rollback user creation
            await UserRepository.delete(user_id)
            return {"success": False, "error": "Failed to create user permission"}
        
        # Assign to group if specified
        if group_id:
            group_assignment_success = await UserGroupAssignmentRepository.create(user_id, group_id)
            if not group_assignment_success:
                logger.warning(f"Failed to assign user {user_id} to group {group_id}")
        
        return {
            "success": True,
            "user_id": user_id,
            "message": f"User '{username}' created successfully with {permission_level} permissions"
        }
        
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        return {"success": False, "error": "Internal server error"}

async def update_user_permissions(user_id: int, permission_level: str = None, is_active: bool = None) -> Dict:
    """
    Update user permissions and active status only (admin only).
    Returns dict with success status and message.
    """
    try:
        # Check if user exists
        user = await UserRepository.get_by_id(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        if is_active is not None:
            # Update active status
            success = await UserRepository.update_is_active(user_id, is_active)
            if not success:
                return {"success": False, "error": "Failed to update user active status"}
        
        if permission_level is not None:
            # Validate permission level
            if permission_level not in ["admin", "manager", "viewer"]:
                return {"success": False, "error": "Invalid permission level. Must be admin, manager, or viewer"}
            
            # Check if permission record exists
            existing_permission = await UserPermissionRepository.get_by_user_id(user_id)
            
            if existing_permission:
                # Update existing permission
                success = await UserPermissionRepository.update(user_id, permission_level)
                if not success:
                    return {"success": False, "error": "Failed to update user permission"}
            else:
                # Create new permission record
                permission_id = await UserPermissionRepository.create(user_id, permission_level)
                if not permission_id:
                    return {"success": False, "error": "Failed to create user permission"}
        
        return {
            "success": True,
            "message": f"User permissions updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating user permissions: {e}")
        return {"success": False, "error": "Internal server error"}

async def delete_admin_user(user_id: int) -> Dict:
    """
    Delete a user (admin only).
    Returns dict with success status and message.
    """
    try:
        # Check if user exists
        user = await UserRepository.get_by_id(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Clean up user sessions
        from app.db.database import db_service
        if db_service.client:
            # Delete user sessions
            await db_service.client.execute(
                "DELETE FROM user_sessions WHERE user_id = ?",
                [user_id]
            )
            
            # Delete refresh tokens
            await db_service.client.execute(
                "DELETE FROM refresh_tokens WHERE user_id = ?",
                [user_id]
            )
        
        # Delete user permission
        await UserPermissionRepository.delete(user_id)
        
        # Delete user group assignments
        if db_service.client:
            await db_service.client.execute(
                "DELETE FROM user_group_assignments WHERE user_id = ?",
                [user_id]
            )
        
        # Delete user
        success = await UserRepository.delete(user_id)
        
        if success:
            return {
                "success": True,
                "message": f"User '{user['username']}' deleted successfully"
            }
        else:
            return {"success": False, "error": "Failed to delete user"}
            
    except Exception as e:
        logger.error(f"Error deleting admin user: {e}")
        return {"success": False, "error": "Internal server error"}

async def update_user_active_status(user_id: int, is_active: bool) -> Dict:
    """
    Update user's active status (admin only).
    Returns dict with success status and message.
    """
    try:
        # Check if user exists
        user = await UserRepository.get_by_id(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Update active status
        success = await UserRepository.update_is_active(user_id, is_active)
        
        if success:
            status = "activated" if is_active else "deactivated"
            return {
                "success": True,
                "message": f"User '{user['username']}' {status} successfully"
            }
        else:
            return {"success": False, "error": "Failed to update user active status"}
            
    except Exception as e:
        logger.error(f"Error updating user active status: {e}")
        return {"success": False, "error": "Internal server error"}

async def get_user_permissions(user_id: int) -> Optional[Dict]:
    """
    Get user permissions (admin only).
    Returns permission dict or None if not found.
    """
    try:
        permission = await UserPermissionRepository.get_by_user_id(user_id)
        return permission
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        return None

async def get_user_groups(user_id: int) -> List[Dict]:
    """
    Get user's group assignments (admin only).
    Returns list of group assignments.
    """
    try:
        groups = await UserGroupAssignmentRepository.get_user_groups(user_id)
        return groups
    except Exception as e:
        logger.error(f"Error getting user groups: {e}")
        return []

async def assign_user_to_group(user_id: int, group_id: int) -> Dict:
    """
    Assign a user to a group (admin only).
    Returns dict with success status and message.
    """
    try:
        # Check if user exists
        user = await UserRepository.get_by_id(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Check if group exists
        group = await UserGroupRepository.get_by_id(group_id)
        if not group:
            return {"success": False, "error": "Group not found"}
        
        # Assign user to group
        assignment_id = await UserGroupAssignmentRepository.create(user_id, group_id)
        
        if assignment_id:
            return {
                "success": True,
                "message": f"User '{user['username']}' assigned to group '{group['name']}' successfully"
            }
        else:
            return {"success": False, "error": "User is already assigned to this group"}
            
    except Exception as e:
        logger.error(f"Error assigning user to group: {e}")
        return {"success": False, "error": "Internal server error"}

async def remove_user_from_group(user_id: int, group_id: int) -> Dict:
    """
    Remove a user from a group (admin only).
    Returns dict with success status and message.
    """
    try:
        # Check if user exists
        user = await UserRepository.get_by_id(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Check if group exists
        group = await UserGroupRepository.get_by_id(group_id)
        if not group:
            return {"success": False, "error": "Group not found"}
        
        # Remove user from group
        success = await UserGroupAssignmentRepository.remove_user_from_group(user_id, group_id)
        
        if success:
            return {
                "success": True,
                "message": f"User '{user['username']}' removed from group '{group['name']}' successfully"
            }
        else:
            return {"success": False, "error": "User is not assigned to this group"}
            
    except Exception as e:
        logger.error(f"Error removing user from group: {e}")
        return {"success": False, "error": "Internal server error"}

async def get_all_user_permissions() -> List[Dict]:
    """
    Get all user permissions efficiently (admin only).
    Returns list of user permissions with user details.
    """
    try:
        # Get all users first
        users = await get_all_users()
        
        # Get permissions for each user
        user_permissions = []
        for user in users:
            permissions = await get_user_permissions(user["id"])
            
            user_permission_data = {
                "user_id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "is_active": user["is_active"],
                "is_admin": user["is_admin"],
                "permission_level": permissions["permission_level"] if permissions else "viewer",
                "permission_created_at": permissions["created_at"] if permissions else None,
                "permission_updated_at": permissions["updated_at"] if permissions else None
            }
            user_permissions.append(user_permission_data)
        
        return user_permissions
        
    except Exception as e:
        logger.error(f"Error getting all user permissions: {e}")
        return []

async def create_user_group(name: str, description: str = None) -> Dict:
    """
    Create a new user group (admin only).
    Returns dict with success status and group ID or error message.
    """
    try:
        if not name or not name.strip():
            return {"success": False, "error": "Group name is required"}
        
        # Check if group name already exists
        existing_groups = await UserGroupRepository.get_all()
        for group in existing_groups:
            if group["name"].lower() == name.strip().lower():
                return {"success": False, "error": "Group name already exists"}
        
        # Create the group
        group_id = await UserGroupRepository.create(name.strip(), description)
        
        if group_id:
            return {
                "success": True,
                "group_id": group_id,
                "message": f"Group '{name}' created successfully"
            }
        else:
            return {"success": False, "error": "Failed to create group"}
            
    except Exception as e:
        logger.error(f"Error creating user group: {e}")
        return {"success": False, "error": "Internal server error"}

async def get_all_user_groups() -> List[Dict]:
    """
    Get all user groups (admin only).
    Returns list of all groups in the system.
    """
    try:
        groups = await UserGroupRepository.get_all()
        return groups
    except Exception as e:
        logger.error(f"Error getting all user groups: {e}")
        return [] 