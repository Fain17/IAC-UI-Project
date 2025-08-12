from app.db.repositories import (
    UserRepository, UserGroupRepository, UserPermissionRepository, 
    UserGroupAssignmentRepository
)
from app.db.models import UserRole
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

async def get_user_by_id(user_id: str) -> Optional[Dict]:
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

async def create_admin_user(username: str, email: str, password: str, role: str = "viewer", group_id: Optional[str] = None) -> Dict:
    """
    Create a new user with admin privileges.
    
    Args:
        username: The username for the new user
        email: The email for the new user
        password: The password for the new user
        role: The role for the new user (admin, manager, viewer)
        group_id: Optional group ID to assign the user to
        
    Returns:
        Dict containing success status and message
    """
    try:
        # Validate role
        if role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER]:
            return {
                "success": False,
                "error": f"Invalid role '{role}'. Must be one of: {', '.join([UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER])}"
            }
        
        # Check if username already exists
        existing_user = await UserRepository.get_by_username(username)
        if existing_user:
            return {
                "success": False,
                "error": f"Username '{username}' already exists"
            }
        
        # Check if email already exists
        existing_email = await UserRepository.get_by_email(email)
        if existing_email:
            return {
                "success": False,
                "error": f"Email '{email}' already exists"
            }
        
        # Hash the password
        hashed_password = auth_service.get_password_hash(password)
        
        # Create the user
        user_id = await UserRepository.create(username, email, hashed_password, is_admin=(role == UserRole.ADMIN))
        if not user_id:
            return {
                "success": False,
                "error": "Failed to create user"
            }
        
        # Create user permissions
        permission_success = await UserPermissionRepository.create(user_id, role)
        if not permission_success:
            # Clean up user if permission creation fails
            await UserRepository.delete(user_id)
            return {
                "success": False,
                "error": "Failed to create user permissions"
            }
        
        # Assign user to group if specified
        if group_id:
            group_success = await UserGroupAssignmentRepository.create(user_id, group_id)
            if not group_success:
                logger.warning(f"Failed to assign user {user_id} to group {group_id}")
        
        return {
            "success": True,
            "user_id": user_id,
            "message": f"User '{username}' created successfully with {role} role"
        }
        
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        return {
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }

async def update_user_permissions(user_id: str, role: str = None, is_active: bool = None, current_admin_id: str = None) -> Dict:
    """
    Update user permissions and active status with security restrictions.
    
    Security Rules:
    1. Admin users (is_admin=true) cannot be downgraded to manager/viewer
    2. Regular users (is_admin=false) can be temporarily elevated to admin
    3. Only admins can change other users' roles
    
    Args:
        user_id: The ID of the user to update
        role: The new role for the user (admin, manager, viewer)
        is_active: The new active status for the user
        current_admin_id: The ID of the admin making the change (for security checks)
        
    Returns:
        Dict containing success status and message
    """
    try:
        # Validate role if provided
        if role is not None:
            if role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER]:
                return {
                    "success": False, "error": f"Invalid role '{role}'. Must be one of: {', '.join([UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER])}"
                }
        
        # Get the target user's current information
        target_user = await UserRepository.get_by_id(user_id)
        if not target_user:
            return {"success": False, "error": "User not found"}
        
        # Get current permissions
        existing_permissions = await UserPermissionRepository.get_by_user_id(user_id)
        current_role = existing_permissions.get("role", "viewer") if existing_permissions else "viewer"
        
        # Security Rule 1: Prevent admin users from being downgraded
        if role is not None and role != UserRole.ADMIN:
            if target_user.get("is_admin", False):
                return {
                    "success": False, 
                    "error": "Cannot downgrade permanent admin users. These users have permanent admin privileges that cannot be revoked."
                }
        
        # Security Rule 2: Check if this is a role elevation (regular user to admin)
        is_role_elevation = False
        if role is not None and role == UserRole.ADMIN:
            if not target_user.get("is_admin", False):
                is_role_elevation = True
                logger.info(f"Elevating user {user_id} from {current_role} to temporary admin role")
        
        # Security Rule 3: Only admins can change roles
        if current_admin_id and role is not None:
            current_admin = await UserRepository.get_by_id(current_admin_id)
            if not current_admin or not current_admin.get("is_admin", False):
                return {
                    "success": False,
                    "error": "Only admin users can change user roles"
                }
        
        # Update user permissions if role is provided
        if role is not None:
            logger.info(f"Updating user {user_id} role from {current_role} to {role}")
            
            if existing_permissions:
                # Update existing permissions
                logger.info(f"Updating existing permissions for user {user_id}")
                success = await UserPermissionRepository.update(user_id, role)
                if not success:
                    logger.error(f"Failed to update permissions for user {user_id}")
                    return {
                        "success": False,
                        "error": "Failed to update user permissions"
                    }
                logger.info(f"Successfully updated permissions for user {user_id}")
            else:
                # Create new permissions
                logger.info(f"Creating new permissions for user {user_id}")
                permission_id = await UserPermissionRepository.create(user_id, role)
                if not permission_id:
                    logger.error(f"Failed to create permissions for user {user_id}")
                    return {
                        "success": False,
                        "error": "Failed to create user permissions"
                    }
                logger.info(f"Successfully created permissions for user {user_id} with ID {permission_id}")
            
            # IMPORTANT: Only update is_admin field if this is a permanent admin (is_admin=true in database)
            # Temporary admins (role=admin but is_admin=false) should keep is_admin=false
            # This allows them to be downgraded later
            if target_user.get("is_admin", False):
                # This is a permanent admin - update is_admin to match role
                is_admin = (role == UserRole.ADMIN)
                logger.info(f"Updating permanent admin is_admin field for user {user_id} to {is_admin}")
                admin_update_success = await UserRepository.update_is_admin(user_id, is_admin)
                if not admin_update_success:
                    logger.warning(f"Failed to update is_admin field for permanent admin {user_id}")
                else:
                    logger.info(f"Successfully updated is_admin field for permanent admin {user_id}")
            else:
                # This is a temporary admin - don't update is_admin field
                # They keep is_admin=false so they can be downgraded later
                logger.info(f"User {user_id} is a temporary admin - keeping is_admin=false for downgrade capability")
        
        # Update user active status if provided
        if is_active is not None:
            success = await UserRepository.update_is_active(user_id, is_active)
            if not success:
                return {
                    "success": False,
                    "error": "Failed to update user active status"
                }
        
        # Prepare response message
        message = "User permissions updated successfully"
        if is_role_elevation:
            message = f"User '{target_user['username']}' has been elevated to temporary admin role. This is a temporary elevation that can be revoked since their permanent admin status (is_admin) remains false."
        elif role == UserRole.ADMIN and target_user.get("is_admin", False):
            message = f"User '{target_user['username']}' is a permanent admin (is_admin=true). Their admin privileges cannot be revoked."
        
        return {
            "success": True,
            "message": message,
            "role_elevated": is_role_elevation,
            "is_permanent_admin": target_user.get("is_admin", False),
            "previous_role": current_role,
            "new_role": role if role else current_role
        }
        
    except Exception as e:
        logger.error(f"Error updating user permissions: {e}")
        return {
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }

async def delete_admin_user(user_id: str) -> Dict:
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

async def update_user_active_status(user_id: str, is_active: bool) -> Dict:
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

async def get_user_permissions(user_id: str) -> Optional[Dict]:
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

async def get_user_groups(user_id: str) -> List[Dict]:
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

async def assign_user_to_group(user_id: str, group_id: str) -> Dict:
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

async def remove_user_from_group(user_id: str, group_id: str) -> Dict:
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
            # Get user permissions
            permissions = await UserPermissionRepository.get_by_user_id(user["id"])
            
            # Get user's group assignments
            user_groups = await UserGroupAssignmentRepository.get_user_groups(user["id"])
            
            # Add permission information to user data
            user_data = {
                **user,
                "role": permissions["role"] if permissions else UserRole.VIEWER,
                "groups": user_groups
            }
            user_permissions.append(user_data)
        
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
        
        # Create the group
        group_id = await UserGroupRepository.create(name.strip(), description)
        if not group_id:
            return {
                "success": False,
                "error": "Failed to create user group"
            }
        
        return {
            "success": True,
            "group_id": group_id,
            "message": f"Group '{name}' created successfully"
        }
            
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

async def get_group_users(group_id: str) -> List[Dict]:
    """Return all users assigned to the specified group (admin only)."""
    try:
        users = await UserGroupAssignmentRepository.get_group_users(group_id)
        return users
    except Exception as e:
        logger.error(f"Error getting users for group {group_id}: {e}")
        return []

async def delete_user_group(group_id: str) -> Dict:
    """
    Delete a user group (admin only).
    This will also remove all user assignments and workflow shares for this group.
    Returns dict with success status and message.
    """
    try:
        # Check if group exists
        group = await UserGroupRepository.get_by_id(group_id)
        if not group:
            return {"success": False, "error": "Group not found"}
        
        # First, remove all users from this group
        from app.db.repositories import UserGroupAssignmentRepository
        group_users = await UserGroupAssignmentRepository.get_group_users(group_id)
        
        # Remove user assignments in a transaction-like manner
        for user in group_users:
            try:
                await UserGroupAssignmentRepository.remove_user_from_group(user["id"], group_id)
            except Exception as e:
                logger.warning(f"Failed to remove user {user['id']} from group {group_id}: {e}")
                # Continue with other users even if one fails
        
        # Remove all workflow shares for this group
        from app.db.database import db_service
        if db_service.client:
            try:
                # First check how many workflow shares exist
                check_result = await db_service.client.execute(
                    "SELECT COUNT(*) FROM workflow_shares WHERE group_id = ?",
                    [group_id]
                )
                share_count = check_result.rows[0][0] if check_result.rows else 0
                
                if share_count > 0:
                    result = await db_service.client.execute(
                        "DELETE FROM workflow_shares WHERE group_id = ?",
                        [group_id]
                    )
                    logger.info(f"Removed {result.rows_affected} workflow shares for group {group_id}")
                else:
                    logger.info(f"No workflow shares found for group {group_id}")
                    
            except Exception as e:
                logger.warning(f"Failed to remove workflow shares for group {group_id}: {e}")
        
        # Now delete the group itself
        logger.info(f"Attempting to delete group {group_id} ({group['name']})")
        success = await UserGroupRepository.delete(group_id)
        
        if success:
            logger.info(f"Successfully deleted group {group_id} ({group['name']})")
            return {
                "success": True,
                "message": f"Group '{group['name']}' deleted successfully. Removed {len(group_users)} user assignments."
            }
        else:
            logger.error(f"Failed to delete group {group_id} ({group['name']})")
            return {"success": False, "error": "Failed to delete group"}
            
    except Exception as e:
        logger.error(f"Error deleting user group: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}

async def update_user_group(group_id: str, name: str = None, description: str = None) -> Dict:
    """
    Update a user group (admin only).
    Updates the name and/or description of an existing group.
    Returns dict with success status and message.
    """
    try:
        # Check if group exists
        group = await UserGroupRepository.get_by_id(group_id)
        if not group:
            return {"success": False, "error": "Group not found"}
        
        # Validate input
        if name is not None and not name.strip():
            return {"success": False, "error": "Group name cannot be empty"}
        
        # Check if new name conflicts with existing group (if name is being changed)
        if name is not None and name.strip() != group["name"]:
            # Check if the new name already exists
            from app.db.repositories import UserGroupRepository
            existing_groups = await UserGroupRepository.get_all()
            for existing_group in existing_groups:
                if existing_group["id"] != group_id and existing_group["name"] == name.strip():
                    return {"success": False, "error": f"Group name '{name.strip()}' already exists"}
        
        # Update the group
        success = await UserGroupRepository.update(
            group_id=group_id,
            name=name.strip() if name else None,
            description=description.strip() if description else None
        )
        
        if success:
            # Get updated group info
            updated_group = await UserGroupRepository.get_by_id(group_id)
            return {
                "success": True,
                "message": f"Group '{group['name']}' updated successfully",
                "group": updated_group
            }
        else:
            return {"success": False, "error": "Failed to update group"}
            
    except Exception as e:
        logger.error(f"Error updating user group: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"} 