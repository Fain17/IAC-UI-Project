from typing import List, Optional, Dict
from app.db.database import db_service, generate_user_id, generate_group_id
from app.db.models import ConfigMapping, User, UserCreate, ConfigMappingCreate
import logging
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

class ConfigMappingRepository:
    """Repository for config mapping operations."""
    
    @staticmethod
    async def get_all() -> Dict[str, str]:
        """Get all mappings from the database."""
        if not db_service.client:
            return {}
        try:
            result = await db_service.client.execute(
                "SELECT instance_name, launch_template_name FROM config_mappings"
            )
            return {str(row[0]): str(row[1]) for row in result.rows}
        except Exception as e:
            logger.error(f"Error loading mappings: {e}")
            return {}
    
    @staticmethod
    async def get_by_instance(instance_name: str) -> Optional[str]:
        """Get launch template name for a specific instance."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "SELECT launch_template_name FROM config_mappings WHERE instance_name = ?",
                [instance_name]
            )
            
            if result.rows:
                return str(result.rows[0][0])
            return None
        except Exception as e:
            logger.error(f"Error getting mapping by instance: {e}")
            return None
    
    @staticmethod
    async def create(instance_name: str, lt_name: str) -> bool:
        """Create a new mapping."""
        if not db_service.client:
            return False
        try:
            # Check if mapping already exists
            result = await db_service.client.execute(
                "SELECT id FROM config_mappings WHERE instance_name = ?",
                [instance_name]
            )
            
            if result.rows:
                return False
            
            # Create new mapping
            await db_service.client.execute(
                "INSERT INTO config_mappings (instance_name, launch_template_name) VALUES (?, ?)",
                [instance_name, lt_name]
            )
            return True
        except Exception as e:
            logger.error(f"Error creating mapping: {e}")
            return False
    
    @staticmethod
    async def update(instance_name: str, lt_name: str) -> bool:
        """Update an existing mapping."""
        if not db_service.client:
            return False
        try:
            # Check if mapping exists
            result = await db_service.client.execute(
                "SELECT id FROM config_mappings WHERE instance_name = ?",
                [instance_name]
            )
            
            if not result.rows:
                return False
            
            # Update mapping
            await db_service.client.execute(
                "UPDATE config_mappings SET launch_template_name = ?, updated_at = CURRENT_TIMESTAMP WHERE instance_name = ?",
                [lt_name, instance_name]
            )
            return True
        except Exception as e:
            logger.error(f"Error updating mapping: {e}")
            return False
    
    @staticmethod
    async def delete(instance_name: str) -> bool:
        """Delete a mapping by instance name."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "DELETE FROM config_mappings WHERE instance_name = ?",
                [instance_name]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting mapping: {e}")
            return False

class UserRepository:
    """Repository for user operations."""
    
    @staticmethod
    async def get_by_id(user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "SELECT id, username, email, is_active, is_admin FROM users WHERE id = ?",
                [user_id]
            )
            
            if not result.rows:
                return None
            
            user = result.rows[0]
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "is_active": user[3],
                "is_admin": user[4]
            }
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    @staticmethod
    async def get_by_username(username: str) -> Optional[Dict]:
        """Get user by username."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "SELECT id, username, email, hashed_password, is_active, is_admin FROM users WHERE username = ? AND is_active = TRUE",
                [username]
            )
            
            if not result.rows:
                return None
            
            user = result.rows[0]
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "hashed_password": user[3],
                "is_active": user[4],
                "is_admin": user[5]
            }
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None

    @staticmethod
    async def get_by_username_including_inactive(username: str) -> Optional[Dict]:
        """Get user by username, including inactive users."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "SELECT id, username, email, hashed_password, is_active, is_admin FROM users WHERE username = ?",
                [username]
            )
            
            if not result.rows:
                return None
            
            user = result.rows[0]
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "hashed_password": user[3],
                "is_active": user[4],
                "is_admin": user[5]
            }
        except Exception as e:
            logger.error(f"Error getting user by username (including inactive): {e}")
            return None

    @staticmethod
    async def get_by_email(email: str) -> Optional[Dict]:
        """Get user by email."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "SELECT id, username, email, hashed_password, is_active, is_admin FROM users WHERE email = ? AND is_active = TRUE",
                [email]
            )
            
            if not result.rows:
                return None
            
            user = result.rows[0]
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "hashed_password": user[3],
                "is_active": user[4],
                "is_admin": user[5]
            }
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None

    @staticmethod
    async def get_by_email_including_inactive(email: str) -> Optional[Dict]:
        """Get user by email, including inactive users."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "SELECT id, username, email, hashed_password, is_active, is_admin FROM users WHERE email = ?",
                [email]
            )
            
            if not result.rows:
                return None
            
            user = result.rows[0]
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "hashed_password": user[3],
                "is_active": user[4],
                "is_admin": user[5]
            }
        except Exception as e:
            logger.error(f"Error getting user by email (including inactive): {e}")
            return None
    
    @staticmethod
    async def create(username: str, email: str, hashed_password: str, is_admin: bool = False) -> Optional[str]:
        """Create a new user and return the user ID."""
        if not db_service.client:
            return None
        try:
            # Check if username already exists
            result = await db_service.client.execute(
                "SELECT id FROM users WHERE username = ?",
                [username]
            )
            
            if result.rows:
                return None
            
            # Check if email already exists
            result = await db_service.client.execute(
                "SELECT id FROM users WHERE email = ?",
                [email]
            )
            
            if result.rows:
                return None
            
            # Generate UUID for user
            user_id = generate_user_id()
            
            # Create new user
            await db_service.client.execute(
                "INSERT INTO users (id, username, email, hashed_password, is_admin) VALUES (?, ?, ?, ?, ?)",
                [user_id, username, email, hashed_password, is_admin]
            )
            return user_id
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    @staticmethod
    async def get_all() -> List[Dict]:
        """Get all users."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute(
                "SELECT id, username, email, is_active, is_admin, created_at, updated_at FROM users ORDER BY username"
            )
            
            users = []
            for row in result.rows:
                users.append({
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "is_active": bool(row[3]),
                    "is_admin": bool(row[4]),
                    "created_at": row[5],
                    "updated_at": row[6]
                })
            return users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    @staticmethod
    async def delete(user_id: str) -> bool:
        """Delete a user."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "DELETE FROM users WHERE id = ?",
                [user_id]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    @staticmethod
    async def update_is_active(user_id: str, is_active: bool) -> bool:
        """Update user's active status."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "UPDATE users SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                [is_active, user_id]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error updating user active status: {e}")
            return False

    @staticmethod
    async def update_is_admin(user_id: str, is_admin: bool) -> bool:
        """Update user's admin status."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "UPDATE users SET is_admin = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                [is_admin, user_id]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error updating user admin status: {e}")
            return False


class RolePermissionRepository:
    """Repository for managing role permissions."""
    
    @staticmethod
    async def get_all() -> List[Dict]:
        """Get all role permissions."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT role, permission, resource_type, created_at, updated_at
                FROM role_permissions
                ORDER BY role, resource_type, permission
            """)
            
            permissions = []
            for row in result.rows:
                permissions.append({
                    "role": row[0],
                    "permission": row[1],
                    "resource_type": row[2],
                    "created_at": row[3],
                    "updated_at": row[4]
                })
            return permissions
        except Exception as e:
            logger.error(f"Error getting all role permissions: {e}")
            return []
    
    @staticmethod
    async def get_by_role(role: str) -> List[Dict]:
        """Get permissions for a specific role."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT role, permission, resource_type, created_at, updated_at
                FROM role_permissions
                WHERE role = ?
                ORDER BY resource_type, permission
            """, [role])
            
            permissions = []
            for row in result.rows:
                permissions.append({
                    "role": row[0],
                    "permission": row[1],
                    "resource_type": row[2],
                    "created_at": row[3],
                    "updated_at": row[4]
                })
            return permissions
        except Exception as e:
            logger.error(f"Error getting permissions for role {role}: {e}")
            return []
    
    @staticmethod
    async def get_by_role_and_resource(role: str, resource_type: str) -> List[Dict]:
        """Get permissions for a specific role and resource type."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT role, permission, resource_type, created_at, updated_at
                FROM role_permissions
                WHERE role = ? AND resource_type = ?
                ORDER BY permission
            """, [role, resource_type])
            
            permissions = []
            for row in result.rows:
                permissions.append({
                    "role": row[0],
                    "permission": row[1],
                    "resource_type": row[2],
                    "created_at": row[3],
                    "updated_at": row[4]
                })
            return permissions
        except Exception as e:
            logger.error(f"Error getting permissions for role {role} and resource {resource_type}: {e}")
            return []

    @staticmethod
    async def get_by_role_grouped(role: str) -> Dict[str, List[str]]:
        """Get permissions for a specific role, grouped by resource type."""
        if not db_service.client:
            return {}
        try:
            result = await db_service.client.execute("""
                SELECT permission, resource_type
                FROM role_permissions
                WHERE role = ?
                ORDER BY resource_type, permission
            """, [role])
            
            grouped_permissions = {}
            for row in result.rows:
                permission, resource_type = row[0], row[1]
                if resource_type not in grouped_permissions:
                    grouped_permissions[resource_type] = []
                grouped_permissions[resource_type].append(permission)
            
            return grouped_permissions
        except Exception as e:
            logger.error(f"Error getting grouped permissions for role {role}: {e}")
            return {}
    
    @staticmethod
    async def add_permission(role: str, permission: str, resource_type: str) -> bool:
        """Add a permission to a role."""
        if not db_service.client:
            return False
        
        # Prevent adding permissions to admin role (admin always has all permissions)
        if role == "admin":
            logger.warning(f"Attempted to add permission {permission} to admin role - operation blocked")
            return False
            
        try:
            result = await db_service.client.execute("""
                INSERT INTO role_permissions (role, permission, resource_type)
                VALUES (?, ?, ?)
            """, [role, permission, resource_type])
            return True
        except Exception as e:
            logger.error(f"Error adding permission {permission} to role {role} for resource {resource_type}: {e}")
            return False
    
    @staticmethod
    async def remove_permission(role: str, permission: str, resource_type: str) -> bool:
        """Remove a permission from a role."""
        if not db_service.client:
            return False
        
        # Prevent removal of admin role permissions
        if role == "admin":
            logger.warning(f"Attempted to remove permission {permission} from admin role - operation blocked")
            return False
            
        try:
            result = await db_service.client.execute("""
                DELETE FROM role_permissions
                WHERE role = ? AND permission = ? AND resource_type = ?
            """, [role, permission, resource_type])
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error removing permission {permission} from role {role} for resource {resource_type}: {e}")
            return False
    
    @staticmethod
    async def ensure_admin_permissions():
        """Ensure admin role always has all permissions on all resources."""
        if not db_service.client:
            return False
            
        try:
            # Define all possible permissions for admin role
            admin_permissions = [
                ("admin", "read", "workflow"),
                ("admin", "write", "workflow"),
                ("admin", "delete", "workflow"),
                ("admin", "execute", "workflow"),
                ("admin", "read", "group"),
                ("admin", "write", "group"),
                ("admin", "delete", "group"),
                ("admin", "execute", "group"),
            ]
            
            # Check and add any missing admin permissions
            for role, permission, resource_type in admin_permissions:
                if not await RolePermissionRepository.has_permission(role, permission, resource_type):
                    await RolePermissionRepository.add_permission(role, permission, resource_type)
                    logger.info(f"Added missing admin permission: {permission} on {resource_type}")
            
            return True
        except Exception as e:
            logger.error(f"Error ensuring admin permissions: {e}")
            return False
    
    @staticmethod
    async def has_permission(role: str, permission: str, resource_type: str) -> bool:
        """Check if a role has a specific permission."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute("""
                SELECT COUNT(*) FROM role_permissions
                WHERE role = ? AND permission = ? AND resource_type = ?
            """, [role, permission, resource_type])
            return result.rows[0][0] > 0
        except Exception as e:
            logger.error(f"Error checking permission {permission} for role {role} on resource {resource_type}: {e}")
            return False
    
    @staticmethod
    async def get_roles() -> List[str]:
        """Get all available roles."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT DISTINCT role FROM role_permissions
                ORDER BY role
            """)
            return [row[0] for row in result.rows]
        except Exception as e:
            logger.error(f"Error getting roles: {e}")
            return []
    
    @staticmethod
    async def get_resource_types() -> List[str]:
        """Get all available resource types."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT DISTINCT resource_type FROM role_permissions
                ORDER BY resource_type
            """)
            return [row[0] for row in result.rows]
        except Exception as e:
            logger.error(f"Error getting resource types: {e}")
            return []
    
    @staticmethod
    async def get_permissions() -> List[str]:
        """Get all available permissions."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT DISTINCT permission FROM role_permissions
                ORDER BY permission
            """)
            return [row[0] for row in result.rows]
        except Exception as e:
            logger.error(f"Error getting permissions: {e}")
            return []

    @staticmethod
    async def clear_all_permissions() -> bool:
        """Clear all role permissions from the table."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute("DELETE FROM role_permissions")
            logger.info(f"Cleared all role permissions. Rows affected: {result.rows_affected}")
            return True
        except Exception as e:
            logger.error(f"Error clearing all role permissions: {e}")
            return False


class WorkflowShareRepository:
    """Repository for managing workflow shares with groups."""
    
    @staticmethod
    async def share(workflow_id: str, group_id: str, permission: str = "read") -> Optional[int]:
        """Share a workflow with a group."""
        if not db_service.client:
            return None
        try:
            # Check if workflow is already shared with this group
            existing_share = await db_service.client.execute("""
                SELECT id, permission FROM workflow_shares
                WHERE workflow_id = ? AND group_id = ?
            """, [workflow_id, group_id])
            
            if existing_share.rows:
                # Update existing share with new permission
                existing_id = existing_share.rows[0][0]
                old_permission = existing_share.rows[0][1]
                
                await db_service.client.execute("""
                    UPDATE workflow_shares 
                    SET permission = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, [permission, existing_id])
                
                logger.info(f"Updated existing workflow share: workflow {workflow_id} with group {group_id}, permission changed from {old_permission} to {permission}")
                return existing_id
            else:
                # Create new share
                result = await db_service.client.execute("""
                    INSERT INTO workflow_shares (workflow_id, group_id, permission)
                    VALUES (?, ?, ?)
                """, [workflow_id, group_id, permission])
                
                if result.rows_affected > 0:
                    # Try to get the ID of the newly inserted row
                    id_result = await db_service.client.execute("""
                        SELECT id FROM workflow_shares 
                        WHERE workflow_id = ? AND group_id = ? 
                        ORDER BY created_at DESC LIMIT 1
                    """, [workflow_id, group_id])
                    
                    if id_result.rows:
                        logger.info(f"Created new workflow share: workflow {workflow_id} with group {group_id}, permission: {permission}")
                        return id_result.rows[0][0]
                    else:
                        logger.info(f"Created new workflow share: workflow {workflow_id} with group {group_id}, permission: {permission}")
                        return True  # Fallback to True if we can't get the ID
                return None
        except Exception as e:
            logger.error(f"Error sharing workflow {workflow_id} with group {group_id}: {e}")
            return None
    
    @staticmethod
    async def unshare(workflow_id: str, group_id: str) -> bool:
        """Remove a workflow's share with a group."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute("""
                DELETE FROM workflow_shares
                WHERE workflow_id = ? AND group_id = ?
            """, [workflow_id, group_id])
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error unsharing workflow {workflow_id} from group {group_id}: {e}")
            return False
    
    @staticmethod
    async def get_by_workflow(workflow_id: str) -> List[Dict]:
        """Get all shares for a specific workflow."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT workflow_id, group_id, permission, created_at, updated_at
                FROM workflow_shares
                WHERE workflow_id = ?
                ORDER BY created_at
            """, [workflow_id])
            
            shares = []
            for row in result.rows:
                shares.append({
                    "workflow_id": row[0],
                    "group_id": row[1],
                    "permission": row[2],
                    "created_at": row[3],
                    "updated_at": row[4]
                })
            return shares
        except Exception as e:
            logger.error(f"Error getting shares for workflow {workflow_id}: {e}")
            return []
    
    @staticmethod
    async def get_by_group(group_id: str) -> List[Dict]:
        """Get all workflows shared with a specific group."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT workflow_id, group_id, permission, created_at, updated_at
                FROM workflow_shares
                WHERE group_id = ?
                ORDER BY created_at
            """, [group_id])
            
            shares = []
            for row in result.rows:
                shares.append({
                    "workflow_id": row[0],
                    "group_id": row[1],
                    "permission": row[2],
                    "created_at": row[3],
                    "updated_at": row[4]
                })
            return shares
        except Exception as e:
            logger.error(f"Error getting shares for group {group_id}: {e}")
            return []
    
    @staticmethod
    async def get_shared_workflows_for_user(user_id: str) -> List[Dict]:
        """Get all workflows shared with groups that the user is a member of."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT DISTINCT ws.workflow_id, ws.group_id, ws.permission, ws.created_at, ws.updated_at
                FROM workflow_shares ws
                JOIN user_group_assignments uga ON ws.group_id = uga.group_id
                WHERE uga.user_id = ?
                ORDER BY ws.created_at
            """, [user_id])
            
            shares = []
            for row in result.rows:
                shares.append({
                    "workflow_id": row[0],
                    "group_id": row[1],
                    "permission": row[2],
                    "created_at": row[3],
                    "updated_at": row[4]
                })
            return shares
        except Exception as e:
            logger.error(f"Error getting shared workflows for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def check_access(workflow_id: str, user_id: str) -> Optional[str]:
        """Check if a user has access to a workflow through group sharing."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute("""
                SELECT ws.permission
                FROM workflow_shares ws
                JOIN user_group_assignments uga ON ws.group_id = uga.group_id
                WHERE ws.workflow_id = ? AND uga.user_id = ?
                LIMIT 1
            """, [workflow_id, user_id])
            
            if result.rows:
                return result.rows[0][0]
            return None
        except Exception as e:
            logger.error(f"Error checking workflow access for user {user_id}: {e}")
            return None
    
    @staticmethod
    async def get_share_info(workflow_id: str, group_id: str) -> Optional[Dict]:
        """Get information about a specific workflow share with a group."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute("""
                SELECT id, workflow_id, group_id, permission, created_at, updated_at
                FROM workflow_shares
                WHERE workflow_id = ? AND group_id = ?
            """, [workflow_id, group_id])
            
            if result.rows:
                row = result.rows[0]
                return {
                    "id": row[0],
                    "workflow_id": row[1],
                    "group_id": row[2],
                    "permission": row[3],
                    "created_at": row[4],
                    "updated_at": row[5]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting share info for workflow {workflow_id} with group {group_id}: {e}")
            return None
    
    @staticmethod
    async def remove_all_for_workflow(workflow_id: str) -> bool:
        """Remove all shares for a specific workflow (useful when deleting workflows)."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute("""
                DELETE FROM workflow_shares
                WHERE workflow_id = ?
            """, [workflow_id])
            return True
        except Exception as e:
            logger.error(f"Error removing all shares for workflow {workflow_id}: {e}")
            return False
    
    @staticmethod
    async def remove_all_for_group(group_id: str) -> bool:
        """Remove all shares for a specific group (useful when deleting groups)."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute("""
                DELETE FROM workflow_shares
                WHERE group_id = ?
            """, [group_id])
            return True
        except Exception as e:
            logger.error(f"Error removing all shares for group {group_id}: {e}")
            return False


class WorkflowScheduleRepository:
    """Repository for managing workflow schedules."""
    
    @staticmethod
    async def get_all() -> List[Dict]:
        """Get all workflow schedules."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT id, workflow_id, user_id, schedule_type, schedule_value, is_active, 
                       continue_on_failure, description, created_at, updated_at, last_execution
                FROM workflow_schedules
                ORDER BY created_at DESC
            """)
            
            schedules = []
            for row in result.rows:
                schedules.append({
                    "id": row[0],
                    "workflow_id": row[1],
                    "user_id": row[2],
                    "schedule_type": row[3],
                    "schedule_value": row[4],
                    "is_active": bool(row[5]),
                    "continue_on_failure": bool(row[6]),
                    "description": row[7],
                    "created_at": row[8],
                    "updated_at": row[9],
                    "last_execution": row[10]
                })
            return schedules
        except Exception as e:
            logger.error(f"Error getting all workflow schedules: {e}")
            return []
    
    @staticmethod
    async def get_all_active() -> List[Dict]:
        """Get all active workflow schedules."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT id, workflow_id, user_id, schedule_type, schedule_value, is_active, 
                       continue_on_failure, description, created_at, updated_at, last_execution
                FROM workflow_schedules
                WHERE is_active = TRUE
                ORDER BY created_at DESC
            """)
            
            schedules = []
            for row in result.rows:
                schedules.append({
                    "id": row[0],
                    "workflow_id": row[1],
                    "user_id": row[2],
                    "schedule_type": row[3],
                    "schedule_value": row[4],
                    "is_active": bool(row[5]),
                    "continue_on_failure": bool(row[6]),
                    "description": row[7],
                    "created_at": row[8],
                    "updated_at": row[9],
                    "last_execution": row[10]
                })
            return schedules
        except Exception as e:
            logger.error(f"Error getting active workflow schedules: {e}")
            return []
    
    @staticmethod
    async def get_by_id(schedule_id: str) -> Optional[Dict]:
        """Get a workflow schedule by ID."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute("""
                SELECT id, workflow_id, user_id, schedule_type, schedule_value, is_active, 
                       continue_on_failure, description, created_at, updated_at, last_execution
                FROM workflow_schedules
                WHERE id = ?
            """, [schedule_id])
            
            if result.rows:
                row = result.rows[0]
                return {
                    "id": row[0],
                    "workflow_id": row[1],
                    "user_id": row[2],
                    "schedule_type": row[3],
                    "schedule_value": row[4],
                    "is_active": bool(row[5]),
                    "continue_on_failure": bool(row[6]),
                    "description": row[7],
                    "created_at": row[8],
                    "updated_at": row[9],
                    "last_execution": row[10]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting workflow schedule {schedule_id}: {e}")
            return None
    
    @staticmethod
    async def get_by_workflow(workflow_id: str) -> List[Dict]:
        """Get all schedules for a specific workflow."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT id, workflow_id, user_id, schedule_type, schedule_value, is_active, 
                       continue_on_failure, description, created_at, updated_at, last_execution
                FROM workflow_schedules
                WHERE workflow_id = ?
                ORDER BY created_at DESC
            """, [workflow_id])
            
            schedules = []
            for row in result.rows:
                schedules.append({
                    "id": row[0],
                    "workflow_id": row[1],
                    "user_id": row[2],
                    "schedule_type": row[3],
                    "schedule_value": row[4],
                    "is_active": bool(row[5]),
                    "continue_on_failure": bool(row[6]),
                    "description": row[7],
                    "created_at": row[8],
                    "updated_at": row[9],
                    "last_execution": row[10]
                })
            return schedules
        except Exception as e:
            logger.error(f"Error getting schedules for workflow {workflow_id}: {e}")
            return []
    
    @staticmethod
    async def get_by_user_id(user_id: str) -> List[Dict]:
        """Get all schedules for a specific user."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT id, workflow_id, user_id, schedule_type, schedule_value, is_active, 
                       continue_on_failure, description, created_at, updated_at, last_execution
                FROM workflow_schedules
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, [user_id])
            
            schedules = []
            for row in result.rows:
                schedules.append({
                    "id": row[0],
                    "workflow_id": row[1],
                    "user_id": row[2],
                    "schedule_type": row[3],
                    "schedule_value": row[4],
                    "is_active": bool(row[5]),
                    "continue_on_failure": bool(row[6]),
                    "description": row[7],
                    "created_at": row[8],
                    "updated_at": row[9],
                    "last_execution": row[10]
                })
            return schedules
        except Exception as e:
            logger.error(f"Error getting schedules for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def create(workflow_id: str, user_id: str, schedule_type: str, schedule_value: str,
                    description: str = None, continue_on_failure: bool = True) -> Optional[str]:
        """Create a new workflow schedule."""
        if not db_service.client:
            return None
        try:
            import uuid
            
            # Generate UUID for schedule ID
            schedule_id = f"schedule_{str(uuid.uuid4())}"
            
            result = await db_service.client.execute("""
                INSERT INTO workflow_schedules (id, workflow_id, user_id, schedule_type, schedule_value,
                                             description, continue_on_failure, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, TRUE)
            """, [schedule_id, workflow_id, user_id, schedule_type, schedule_value, description, continue_on_failure])
            
            if result.rows_affected > 0:
                return schedule_id
            return None
        except Exception as e:
            logger.error(f"Error creating workflow schedule: {e}")
            return None
    
    @staticmethod
    async def update(schedule_id: str, schedule_type: str = None, schedule_value: str = None,
                    description: str = None, is_active: bool = None, continue_on_failure: bool = None) -> bool:
        """Update a workflow schedule."""
        if not db_service.client:
            return False
        try:
            update_fields = []
            params = []
            
            if schedule_type is not None:
                update_fields.append("schedule_type = ?")
                params.append(schedule_type)
            
            if schedule_value is not None:
                update_fields.append("schedule_value = ?")
                params.append(schedule_value)
            
            if description is not None:
                update_fields.append("description = ?")
                params.append(description)
            
            if is_active is not None:
                update_fields.append("is_active = ?")
                params.append(is_active)
            
            if continue_on_failure is not None:
                update_fields.append("continue_on_failure = ?")
                params.append(continue_on_failure)
            
            if not update_fields:
                return True  # Nothing to update
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(schedule_id)
            
            query = f"""
                UPDATE workflow_schedules 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """
            
            result = await db_service.client.execute(query, params)
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error updating workflow schedule {schedule_id}: {e}")
            return False
    
    @staticmethod
    async def update_last_execution(schedule_id: str, execution_time: datetime) -> bool:
        """Update the last execution time of a schedule."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute("""
                UPDATE workflow_schedules 
                SET last_execution = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, [execution_time.isoformat(), schedule_id])
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error updating last execution for schedule {schedule_id}: {e}")
            return False
    
    @staticmethod
    async def delete(schedule_id: str) -> bool:
        """Delete a workflow schedule."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute("""
                DELETE FROM workflow_schedules WHERE id = ?
            """, [schedule_id])
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting workflow schedule {schedule_id}: {e}")
            return False
    
    @staticmethod
    async def validate_schedule(schedule_type: str, schedule_value: str) -> bool:
        """Validate a schedule type and value."""
        try:
            if schedule_type == "interval":
                # Validate interval format (e.g., "30m", "2h", "1d")
                if not schedule_value or len(schedule_value) < 2:
                    return False
                value = int(schedule_value[:-1])
                unit = schedule_value[-1].lower()
                return unit in ['m', 'h', 'd'] and value > 0
            
            elif schedule_type == "daily":
                # Validate time format (e.g., "09:00", "14:30")
                if not schedule_value or ':' not in schedule_value:
                    return False
                hour, minute = map(int, schedule_value.split(':'))
                return 0 <= hour <= 23 and 0 <= minute <= 59
            
            elif schedule_type == "weekly":
                # Validate day:time format (e.g., "monday:09:00")
                if not schedule_value or ':' not in schedule_value:
                    return False
                day_str, time_str = schedule_value.split(':', 1)
                valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                if day_str.lower() not in valid_days:
                    return False
                # Validate time part
                if ':' not in time_str:
                    return False
                hour, minute = map(int, time_str.split(':'))
                return 0 <= hour <= 23 and 0 <= minute <= 59
            
            elif schedule_type == "monthly":
                # Validate day:time format (e.g., "15:09:00")
                if not schedule_value or ':' not in schedule_value:
                    return False
                day_str, time_str = schedule_value.split(':', 1)
                day = int(day_str)
                if day < 1 or day > 31:
                    return False
                # Validate time part
                if ':' not in time_str:
                    return False
                hour, minute = map(int, time_str.split(':'))
                return 0 <= hour <= 23 and 0 <= minute <= 59
            
            return False
        except Exception:
            return False


class UserSessionRepository:
    """Repository for user session operations."""
    @staticmethod
    async def create(user_id: str, session_token: str, expires_at):
        if not db_service.client:
            return False
        try:
            await db_service.client.execute(
                "INSERT INTO user_sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)",
                [user_id, session_token, expires_at]
            )
            return True
        except Exception as e:
            logger.error(f"Error creating user session: {e}")
            return False

    @staticmethod
    async def delete_by_token(session_token: str) -> bool:
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "DELETE FROM user_sessions WHERE session_token = ?",
                [session_token]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting user session: {e}")
            return False

    @staticmethod
    async def exists(session_token: str) -> bool:
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "SELECT id FROM user_sessions WHERE session_token = ?",
                [session_token]
            )
            return bool(result.rows)
        except Exception as e:
            logger.error(f"Error checking user session: {e}")
            return False

    @staticmethod
    async def get_all_for_user(user_id: str) -> List[Dict]:
        """Get all active sessions for a user."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute(
                "SELECT id, session_token, expires_at, created_at FROM user_sessions WHERE user_id = ?",
                [user_id]
            )
            return [
                {
                    "id": row[0],
                    "session_token": row[1],
                    "expires_at": row[2],
                    "created_at": row[3]
                }
                for row in result.rows
            ]
        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {e}")
            return []

    @staticmethod
    async def delete_all_for_user(user_id: str) -> bool:
        """Delete all sessions for a user."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "DELETE FROM user_sessions WHERE user_id = ?",
                [user_id]
            )
            deleted_count = result.rows_affected
            logger.info(f"Deleted {deleted_count} sessions for user {user_id}")
            return deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting sessions for user {user_id}: {e}")
            return False

    @staticmethod
    async def get_all_active_sessions() -> List[Dict]:
        """Get all active sessions."""
        if not db_service.client:
            return []
        try:
            current_time = datetime.now(timezone.utc).isoformat()
            result = await db_service.client.execute(
                "SELECT user_id, session_token, expires_at FROM user_sessions WHERE expires_at > ?",
                [current_time]
            )
            return [
                {
                    "user_id": row[0],
                    "session_token": row[1],
                    "expires_at": row[2]
                }
                for row in result.rows
            ]
        except Exception as e:
            logger.error(f"Error getting all active sessions: {e}")
            return [] 

class RefreshTokenRepository:
    """Repository for refresh token operations."""
    
    @staticmethod
    async def create(user_id: str, refresh_token: str, expires_at) -> bool:
        """Create a new refresh token."""
        if not db_service.client:
            return False
        try:
            await db_service.client.execute(
                "INSERT INTO refresh_tokens (user_id, refresh_token, expires_at) VALUES (?, ?, ?)",
                [user_id, refresh_token, expires_at]
            )
            logger.info(f"Refresh token created in database for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            return False

    @staticmethod
    async def get_by_token(refresh_token: str) -> Optional[Dict]:
        """Get refresh token info by token."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "SELECT user_id, expires_at, is_revoked FROM refresh_tokens WHERE refresh_token = ?",
                [refresh_token]
            )
            
            if not result.rows:
                return None
            
            user_id, expires_at, is_revoked = result.rows[0]
            return {
                "user_id": user_id,
                "expires_at": expires_at,
                "is_revoked": bool(is_revoked)
            }
        except Exception as e:
            logger.error(f"Error getting refresh token: {e}")
            return None

    @staticmethod
    async def delete_by_token(refresh_token: str) -> bool:
        """Delete a refresh token by token."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "DELETE FROM refresh_tokens WHERE refresh_token = ?",
                [refresh_token]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting refresh token: {e}")
            return False

    @staticmethod
    async def revoke_by_token(refresh_token: str) -> bool:
        """Revoke a refresh token by setting is_revoked to TRUE."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "UPDATE refresh_tokens SET is_revoked = TRUE WHERE refresh_token = ?",
                [refresh_token]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error revoking refresh token: {e}")
            return False

    @staticmethod
    async def revoke_all_for_user(user_id: str) -> bool:
        """Revoke all refresh tokens for a specific user."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "UPDATE refresh_tokens SET is_revoked = TRUE WHERE user_id = ?",
                [user_id]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error revoking all refresh tokens for user {user_id}: {e}")
            return False

    @staticmethod
    async def cleanup_expired() -> int:
        """Clean up expired refresh tokens."""
        if not db_service.client:
            return 0
        try:
            result = await db_service.client.execute(
                "DELETE FROM refresh_tokens WHERE expires_at < ?",
                [datetime.now(timezone.utc).isoformat()]
            )
            return result.rows_affected
        except Exception as e:
            logger.error(f"Error cleaning up expired refresh tokens: {e}")
            return 0

class UserGroupRepository:
    """Repository for user group operations."""
    
    @staticmethod
    async def create(name: str, description: str = None) -> Optional[str]:
        """Create a new user group and return the group ID."""
        if not db_service.client:
            return None
        try:
            # Check if group already exists
            result = await db_service.client.execute(
                "SELECT id FROM user_groups WHERE name = ?",
                [name]
            )
            
            if result.rows:
                return None
            
            # Generate UUID for group
            group_id = generate_group_id()
            
            # Create new group
            await db_service.client.execute(
                "INSERT INTO user_groups (id, name, description) VALUES (?, ?, ?)",
                [group_id, name, description]
            )
            return group_id
        except Exception as e:
            logger.error(f"Error creating user group: {e}")
            return None
    
    @staticmethod
    async def get_by_id(group_id: str) -> Optional[Dict]:
        """Get user group by ID."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "SELECT id, name, description, created_at, updated_at FROM user_groups WHERE id = ?",
                [group_id]
            )
            
            if not result.rows:
                return None
            
            group = result.rows[0]
            return {
                "id": group[0],
                "name": group[1],
                "description": group[2],
                "created_at": group[3],
                "updated_at": group[4]
            }
        except Exception as e:
            logger.error(f"Error getting user group by ID: {e}")
            return None
    
    @staticmethod
    async def get_all() -> List[Dict]:
        """Get all user groups."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute(
                "SELECT id, name, description, created_at, updated_at FROM user_groups ORDER BY name"
            )
            
            groups = []
            for row in result.rows:
                groups.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "created_at": row[3],
                    "updated_at": row[4]
                })
            return groups
        except Exception as e:
            logger.error(f"Error getting all user groups: {e}")
            return []
    
    @staticmethod
    async def update(group_id: str, name: str = None, description: str = None) -> bool:
        """Update a user group."""
        if not db_service.client:
            return False
        try:
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            if not updates:
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(group_id)
            
            query = f"UPDATE user_groups SET {', '.join(updates)} WHERE id = ?"
            result = await db_service.client.execute(query, params)
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error updating user group: {e}")
            return False
    
    @staticmethod
    async def get_members(group_id: str) -> List[Dict]:
        """Get all members of a user group."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT uga.user_id, uga.group_id, uga.created_at,
                       u.username, u.email, u.is_active
                FROM user_group_assignments uga
                JOIN users u ON uga.user_id = u.id
                WHERE uga.group_id = ?
                ORDER BY u.username
            """, [group_id])
            
            members = []
            for row in result.rows:
                members.append({
                    "user_id": row[0],
                    "group_id": row[1],
                    "assigned_at": row[2],
                    "username": row[3],
                    "email": row[4],
                    "is_active": bool(row[5])
                })
            return members
        except Exception as e:
            logger.error(f"Error getting members for group {group_id}: {e}")
            return []
    
    @staticmethod
    async def delete(group_id: str) -> bool:
        """Delete a user group."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "DELETE FROM user_groups WHERE id = ?",
                [group_id]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting user group: {e}")
            return False

class UserPermissionRepository:
    """Repository for user permission operations."""
    
    @staticmethod
    async def create(user_id: str, role: str) -> Optional[int]:
        """Create a new user permission record."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "INSERT INTO user_permissions (user_id, role) VALUES (?, ?)",
                [user_id, role]
            )
            return int(result.last_insert_rowid) if result.last_insert_rowid else None
        except Exception as e:
            logger.error(f"Error creating user permission: {e}")
            return None
    
    @staticmethod
    async def get_by_user_id(user_id: str) -> Optional[Dict]:
        """Get user permission by user ID."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "SELECT id, user_id, role, created_at, updated_at FROM user_permissions WHERE user_id = ?",
                [user_id]
            )
            
            if not result.rows:
                return None
            
            permission = result.rows[0]
            return {
                "id": permission[0],
                "user_id": permission[1],
                "role": permission[2],
                "created_at": permission[3],
                "updated_at": permission[4]
            }
        except Exception as e:
            logger.error(f"Error getting user permission: {e}")
            return None
    
    @staticmethod
    async def update(user_id: str, role: str) -> bool:
        """Update user permission."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "UPDATE user_permissions SET role = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                [role, user_id]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error updating user permission: {e}")
            return False
    
    @staticmethod
    async def delete(user_id: str) -> bool:
        """Delete user permission."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "DELETE FROM user_permissions WHERE user_id = ?",
                [user_id]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting user permission: {e}")
            return False

    @staticmethod
    async def get_all() -> List[Dict]:
        """Get all user permissions."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT up.user_id, up.role, up.created_at, up.updated_at,
                       u.username, u.email, u.is_active, u.is_admin
                FROM user_permissions up
                JOIN users u ON up.user_id = u.id
                ORDER BY u.username
            """)
            
            permissions = []
            for row in result.rows:
                permissions.append({
                    "user_id": row[0],
                    "role": row[1],
                    "created_at": row[2],
                    "updated_at": row[3],
                    "username": row[4],
                    "email": row[5],
                    "is_active": bool(row[6]),
                    "is_admin": bool(row[7])
                })
            return permissions
        except Exception as e:
            logger.error(f"Error getting all user permissions: {e}")
            return []

class UserGroupAssignmentRepository:
    """Repository for user group assignment operations."""
    
    @staticmethod
    async def create(user_id: str, group_id: str) -> Optional[int]:
        """Assign a user to a group and return the assignment ID."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "INSERT INTO user_group_assignments (user_id, group_id) VALUES (?, ?) RETURNING id",
                [user_id, group_id]
            )
            return result.rows[0][0] if result.rows else None
        except Exception as e:
            logger.error(f"Error creating user group assignment: {e}")
            return None
    
    @staticmethod
    async def get_user_groups(user_id: str) -> List[Dict]:
        """Get all groups for a user."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT ug.id, ug.name, ug.description, uga.created_at 
                FROM user_groups ug 
                JOIN user_group_assignments uga ON ug.id = uga.group_id 
                WHERE uga.user_id = ?
            """, [user_id])
            
            groups = []
            for row in result.rows:
                groups.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "assigned_at": row[3]
                })
            return groups
        except Exception as e:
            logger.error(f"Error getting user groups: {e}")
            return []
    
    @staticmethod
    async def get_group_users(group_id: str) -> List[Dict]:
        """Get all users in a group."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute("""
                SELECT u.id, u.username, u.email, u.is_active, uga.created_at 
                FROM users u 
                JOIN user_group_assignments uga ON u.id = uga.user_id 
                WHERE uga.group_id = ?
            """, [group_id])
            
            users = []
            for row in result.rows:
                users.append({
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "is_active": bool(row[3]),
                    "assigned_at": row[4]
                })
            return users
        except Exception as e:
            logger.error(f"Error getting group users: {e}")
            return []
    
    @staticmethod
    async def remove_user_from_group(user_id: str, group_id: str) -> bool:
        """Remove a user from a group."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "DELETE FROM user_group_assignments WHERE user_id = ? AND group_id = ?",
                [user_id, group_id]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error removing user from group: {e}")
            return False

class WorkflowRepository:
    """Repository for workflow operations."""
    
    @staticmethod
    async def create(workflow_id: str, user_id: str, name: str, description: str = None, steps: List[Dict] = None) -> bool:
        """Create a new workflow and return success status."""
        if not db_service.client:
            return False
        try:
            # Convert steps to JSON string
            steps_json = json.dumps(steps or [])
            
            result = await db_service.client.execute(
                "INSERT INTO workflows (id, user_id, name, description, steps) VALUES (?, ?, ?, ?, ?)",
                [workflow_id, user_id, name, description, steps_json]
            )
            
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            return False
    
    @staticmethod
    async def get_by_id(workflow_id: str, user_id: str) -> Optional[Dict]:
        """Get workflow by ID for a specific user (including shared workflows)."""
        if not db_service.client:
            return None
        try:
            # First check if user owns the workflow directly
            result = await db_service.client.execute(
                "SELECT id, user_id, name, description, steps, is_active, created_at, updated_at FROM workflows WHERE id = ? AND user_id = ?",
                [workflow_id, user_id]
            )
            
            if result.rows:
                workflow = result.rows[0]
                return {
                    "id": workflow[0],
                    "user_id": workflow[1],
                    "name": workflow[2],
                    "description": workflow[3],
                    "steps": json.loads(workflow[4]),
                    "is_active": bool(workflow[5]),
                    "created_at": workflow[6],
                    "updated_at": workflow[7]
                }
            
            # If not owner, check if workflow is shared with user's groups
            result = await db_service.client.execute("""
                SELECT DISTINCT w.id, w.user_id, w.name, w.description, w.steps, w.is_active, w.created_at, w.updated_at
                FROM workflows w
                JOIN workflow_shares ws ON w.id = ws.workflow_id
                JOIN user_group_assignments uga ON ws.group_id = uga.group_id
                WHERE uga.user_id = ? AND w.id = ? AND w.is_active = TRUE
            """, [user_id, workflow_id])
            
            if result.rows:
                workflow = result.rows[0]
                return {
                    "id": workflow[0],
                    "user_id": workflow[1],
                    "name": workflow[2],
                    "description": workflow[3],
                    "steps": json.loads(workflow[4]),
                    "is_active": bool(workflow[5]),
                    "created_at": workflow[6],
                    "updated_at": workflow[7]
                }
            
            return None
        except Exception as e:
            logger.error(f"Error getting workflow by ID: {e}")
            return None

    @staticmethod
    async def get_user_workflow_permissions(workflow_id: str, user_id: str) -> Dict[str, str]:
        """
        Get user's permissions for a specific workflow.
        Returns dict with 'access_type' and 'permissions'.
        """
        if not db_service.client:
            return {"access_type": "none", "permissions": []}
        
        try:
            # Check if user owns the workflow
            result = await db_service.client.execute(
                "SELECT user_id FROM workflows WHERE id = ? AND user_id = ?",
                [workflow_id, user_id]
            )
            
            if result.rows:
                return {
                    "access_type": "owner",
                    "permissions": ["read", "write", "execute", "delete", "share"]
                }
            
            # Check shared access through groups
            result = await db_service.client.execute("""
                SELECT ws.permission
                FROM workflow_shares ws
                JOIN user_group_assignments uga ON ws.group_id = uga.group_id
                WHERE uga.user_id = ? AND ws.workflow_id = ?
            """, [user_id, workflow_id])
            
            if result.rows:
                # Get all permissions from shared access
                permissions = [row[0] for row in result.rows]
                return {
                    "access_type": "shared",
                    "permissions": permissions
                }
            
            return {"access_type": "none", "permissions": []}
            
        except Exception as e:
            logger.error(f"Error getting user workflow permissions: {e}")
            return {"access_type": "none", "permissions": []}
    
    @staticmethod
    async def get_by_id_admin(workflow_id: str) -> Optional[Dict]:
        """Get workflow by ID without user restriction (admin use)."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "SELECT id, user_id, name, description, steps, is_active, created_at, updated_at FROM workflows WHERE id = ?",
                [workflow_id]
            )
            
            if not result.rows:
                return None
            
            workflow = result.rows[0]
            return {
                "id": workflow[0],
                "user_id": workflow[1],
                "name": workflow[2],
                "description": workflow[3],
                "steps": json.loads(workflow[4]),
                "is_active": bool(workflow[5]),
                "created_at": workflow[6],
                "updated_at": workflow[7]
            }
        except Exception as e:
            logger.error(f"Error getting workflow by ID (admin): {e}")
            return None
    
    @staticmethod
    async def get_all_by_user(user_id: str) -> List[Dict]:
        """Get all workflows for a specific user."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute(
                "SELECT id, user_id, name, description, steps, is_active, created_at, updated_at FROM workflows WHERE user_id = ? ORDER BY created_at DESC",
                [user_id]
            )
            
            workflows = []
            for row in result.rows:
                workflows.append({
                    "id": row[0],
                    "user_id": row[1],
                    "name": row[2],
                    "description": row[3],
                    "steps": json.loads(row[4]),
                    "is_active": bool(row[5]),
                    "created_at": row[6],
                    "updated_at": row[7]
                })
            return workflows
        except Exception as e:
            logger.error(f"Error getting workflows for user: {e}")
            return []
    
    @staticmethod
    async def get_all_by_user_groups(user_id: str, group_id: str = None) -> List[Dict]:
        """Get all workflows accessible to a user through team/group membership."""
        if not db_service.client:
            return []
        try:
            # If group_id is provided, get workflows from that specific group
            if group_id:
                result = await db_service.client.execute("""
                    SELECT DISTINCT w.id, w.user_id, w.name, w.description, w.steps, w.is_active, w.created_at, w.updated_at
                    FROM workflows w
                    JOIN user_group_assignments uga ON w.user_id = uga.user_id
                    WHERE uga.group_id = ? AND w.is_active = TRUE
                    ORDER BY w.created_at DESC
                """, [group_id])
            else:
                # Get workflows from all groups the user is a member of
                result = await db_service.client.execute("""
                    SELECT DISTINCT w.id, w.user_id, w.name, w.description, w.steps, w.is_active, w.created_at, w.updated_at
                    FROM workflows w
                    JOIN user_group_assignments uga ON w.user_id = uga.user_id
                    JOIN user_group_assignments user_uga ON user_uga.group_id = uga.group_id
                    WHERE user_uga.user_id = ? AND w.is_active = TRUE
                    ORDER BY w.created_at DESC
                """, [user_id])
            
            workflows = []
            for row in result.rows:
                workflows.append({
                    "id": row[0],
                    "user_id": row[1],
                    "name": row[2],
                    "description": row[3],
                    "steps": json.loads(row[4]),
                    "is_active": bool(row[5]),
                    "created_at": row[6],
                    "updated_at": row[7]
                })
            return workflows
        except Exception as e:
            logger.error(f"Error getting workflows by user groups: {e}")
            return []
    
    @staticmethod
    async def delete(workflow_id: str, user_id: str) -> bool:
        """Delete a workflow by ID for a specific user."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "DELETE FROM workflows WHERE id = ? AND user_id = ?",
                [workflow_id, user_id]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting workflow: {e}")
            return False
    
    @staticmethod
    async def update(workflow_id: str, user_id: str, name: str = None, description: str = None, steps: List[Dict] = None, is_active: bool = None) -> bool:
        """Update a workflow by ID for a specific user."""
        if not db_service.client:
            return False
        try:
            # Build dynamic update query
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if steps is not None:
                updates.append("steps = ?")
                params.append(json.dumps(steps))
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(is_active)
            
            if not updates:
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.extend([workflow_id, user_id])
            
            query = f"UPDATE workflows SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
            result = await db_service.client.execute(query, params)
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error updating workflow: {e}")
            return False 


class DockerMappingRepository:
    """Repository for managing docker execution mappings."""
    
    @staticmethod
    async def create(script_type: str, docker_image: str, docker_tag: str = "latest",
                    description: str = None, environment_variables: Dict = None,
                    volumes: List[str] = None, ports: List[str] = None,
                    is_active: bool = True, created_by: str = None) -> Optional[str]:
        """Create a new docker execution mapping."""
        if not db_service.client:
            return None
        try:
            import uuid
            mapping_id = f"docker_mapping_{str(uuid.uuid4())}"
            
            result = await db_service.client.execute("""
                INSERT INTO docker_mappings (
                    id, script_type, docker_image, docker_tag, description,
                    environment_variables, volumes, ports, is_active, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                mapping_id, script_type, docker_image, docker_tag, description,
                json.dumps(environment_variables or {}),
                json.dumps(volumes or []),
                json.dumps(ports or []),
                is_active, created_by
            ])
            
            if result.rows_affected > 0:
                logger.info(f"Created docker mapping: {script_type} -> {docker_image}:{docker_tag}")
                return mapping_id
            return None
        except Exception as e:
            logger.error(f"Error creating docker mapping: {e}")
            return None
    
    @staticmethod
    async def get_by_id(mapping_id: str) -> Optional[Dict]:
        """Get docker mapping by ID."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute("""
                SELECT id, script_type, docker_image, docker_tag, description,
                       environment_variables, volumes, ports, is_active, created_by,
                       created_at, updated_at
                FROM docker_mappings WHERE id = ?
            """, [mapping_id])
            
            if not result.rows:
                return None
            
            row = result.rows[0]
            return {
                "id": row[0],
                "script_type": row[1],
                "docker_image": row[2],
                "docker_tag": row[3],
                "description": row[4],
                "environment_variables": json.loads(row[5]) if row[5] else {},
                "volumes": json.loads(row[6]) if row[6] else [],
                "ports": json.loads(row[7]) if row[7] else [],
                "is_active": bool(row[8]),
                "created_by": row[9],
                "created_at": row[10],
                "updated_at": row[11]
            }
        except Exception as e:
            logger.error(f"Error getting docker mapping by ID: {e}")
            return None
    
    @staticmethod
    async def get_all(script_type: str = None, is_active: bool = None) -> List[Dict]:
        """Get all docker mappings with optional filtering."""
        if not db_service.client:
            return []
        try:
            query = "SELECT id, script_type, docker_image, docker_tag, description, environment_variables, volumes, ports, is_active, created_by, created_at, updated_at FROM docker_mappings"
            params = []
            
            if script_type or is_active is not None:
                query += " WHERE"
                conditions = []
                
                if script_type:
                    conditions.append("script_type = ?")
                    params.append(script_type)
                
                if is_active is not None:
                    conditions.append("is_active = ?")
                    params.append(is_active)
                
                query += " " + " AND ".join(conditions)
            
            query += " ORDER BY script_type, created_at DESC"
            
            result = await db_service.client.execute(query, params)
            
            mappings = []
            for row in result.rows:
                mappings.append({
                    "id": row[0],
                    "script_type": row[1],
                    "docker_image": row[2],
                    "docker_tag": row[3],
                    "description": row[4],
                    "environment_variables": json.loads(row[5]) if row[5] else {},
                    "volumes": json.loads(row[6]) if row[6] else [],
                    "ports": json.loads(row[7]) if row[7] else [],
                    "is_active": bool(row[8]),
                    "created_by": row[9],
                    "created_at": row[10],
                    "updated_at": row[11]
                })
            
            return mappings
        except Exception as e:
            logger.error(f"Error getting all docker mappings: {e}")
            return []
    
    @staticmethod
    async def update(mapping_id: str, **kwargs) -> bool:
        """Update a docker mapping."""
        if not db_service.client:
            return False
        try:
            updates = []
            params = []
            
            for key, value in kwargs.items():
                if key in ["script_type", "docker_image", "docker_tag", "description", "is_active"]:
                    updates.append(f"{key} = ?")
                    params.append(value)
                elif key in ["environment_variables", "volumes", "ports"]:
                    updates.append(f"{key} = ?")
                    params.append(json.dumps(value))
            
            if not updates:
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(mapping_id)
            
            query = f"UPDATE docker_mappings SET {', '.join(updates)} WHERE id = ?"
            result = await db_service.client.execute(query, params)
            
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error updating docker mapping: {e}")
            return False
    
    @staticmethod
    async def delete(mapping_id: str) -> bool:
        """Delete a docker mapping."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "DELETE FROM docker_mappings WHERE id = ?",
                [mapping_id]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting docker mapping: {e}")
            return False

    @staticmethod
    async def get_image_for_type(script_type: str) -> Optional[str]:
        """Get the most recent active Docker image for a script type."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute("""
                SELECT docker_image, docker_tag FROM docker_mappings 
                WHERE script_type = ? AND is_active = 1 
                ORDER BY updated_at DESC, created_at DESC 
                LIMIT 1
            """, [script_type])
            
            if result.rows:
                docker_image = result.rows[0][0]
                docker_tag = result.rows[0][1]
                return f"{docker_image}:{docker_tag}"
            return None
        except Exception as e:
            logger.error(f"Error getting Docker image for type {script_type}: {e}")
            return None


class ResourceMappingRepository:
    """Repository for managing custom resource mappings."""
    
    @staticmethod
    async def create(mapping_type: str, source_resource: str, target_resource: str,
                    description: str = None, metadata: Dict = None,
                    is_active: bool = True, created_by: str = None) -> Optional[str]:
        """Create a new resource mapping."""
        if not db_service.client:
            return None
        try:
            import uuid
            mapping_id = f"resource_mapping_{str(uuid.uuid4())}"
            
            result = await db_service.client.execute("""
                INSERT INTO resource_mappings (
                    id, mapping_type, source_resource, target_resource, description,
                    metadata, is_active, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                mapping_id, mapping_type, source_resource, target_resource, description,
                json.dumps(metadata or {}),
                is_active, created_by
            ])
            
            if result.rows_affected > 0:
                logger.info(f"Created resource mapping: {mapping_type} -> {source_resource} -> {target_resource}")
                return mapping_id
            return None
        except Exception as e:
            logger.error(f"Error creating resource mapping: {e}")
            return None
    
    @staticmethod
    async def get_by_id(mapping_id: str) -> Optional[Dict]:
        """Get resource mapping by ID."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute("""
                SELECT id, mapping_type, source_resource, target_resource, description,
                       metadata, is_active, created_by, created_at, updated_at
                FROM resource_mappings WHERE id = ?
            """, [mapping_id])
            
            if not result.rows:
                return None
            
            row = result.rows[0]
            return {
                "id": row[0],
                "mapping_type": row[1],
                "source_resource": row[2],
                "target_resource": row[3],
                "description": row[4],
                "metadata": json.loads(row[5]) if row[5] else {},
                "is_active": bool(row[6]),
                "created_by": row[7],
                "created_at": row[8],
                "updated_at": row[9]
            }
        except Exception as e:
            logger.error(f"Error getting resource mapping by ID: {e}")
            return None
    
    @staticmethod
    async def get_all(mapping_type: str = None, source_resource: str = None, is_active: bool = None) -> List[Dict]:
        """Get all resource mappings with optional filtering."""
        if not db_service.client:
            return []
        try:
            query = "SELECT id, mapping_type, source_resource, target_resource, description, metadata, is_active, created_by, created_at, updated_at FROM resource_mappings"
            params = []
            
            if mapping_type or source_resource or is_active is not None:
                query += " WHERE"
                conditions = []
                
                if mapping_type:
                    conditions.append("mapping_type = ?")
                    params.append(mapping_type)
                
                if source_resource:
                    conditions.append("source_resource = ?")
                    params.append(source_resource)
                
                if is_active is not None:
                    conditions.append("is_active = ?")
                    params.append(is_active)
                
                query += " " + " AND ".join(conditions)
            
            query += " ORDER BY mapping_type, created_at DESC"
            
            result = await db_service.client.execute(query, params)
            
            mappings = []
            for row in result.rows:
                mappings.append({
                    "id": row[0],
                    "mapping_type": row[1],
                    "source_resource": row[2],
                    "target_resource": row[3],
                    "description": row[4],
                    "metadata": json.loads(row[5]) if row[5] else {},
                    "is_active": bool(row[6]),
                    "created_by": row[7],
                    "created_at": row[8],
                    "updated_at": row[9]
                })
            
            return mappings
        except Exception as e:
            logger.error(f"Error getting all resource mappings: {e}")
            return []
    
    @staticmethod
    async def update(mapping_id: str, **kwargs) -> bool:
        """Update a resource mapping."""
        if not db_service.client:
            return False
        try:
            updates = []
            params = []
            
            for key, value in kwargs.items():
                if key in ["mapping_type", "source_resource", "target_resource", "description", "is_active"]:
                    updates.append(f"{key} = ?")
                    params.append(value)
                elif key == "metadata":
                    updates.append("metadata = ?")
                    params.append(json.dumps(value))
            
            if not updates:
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(mapping_id)
            
            query = f"UPDATE resource_mappings SET {', '.join(updates)} WHERE id = ?"
            result = await db_service.client.execute(query, params)
            
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error updating resource mapping: {e}")
            return False
    
    @staticmethod
    async def delete(mapping_id: str) -> bool:
        """Delete a resource mapping."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "DELETE FROM resource_mappings WHERE id = ?",
                [mapping_id]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting resource mapping: {e}")
            return False 

class VaultConfigRepository:
    """Repository for HashiCorp Vault configuration operations."""
    
    @staticmethod
    async def create(
        config_name: str,
        vault_address: str,
        vault_token: str,
        mount_path: str,
        engine_type: str,
        engine_version: str,
        created_by: str,
        namespace: str = None,
        is_active: bool = True
    ) -> Optional[int]:
        """Create a new vault configuration."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                """INSERT INTO vault_configs 
                   (config_name, vault_address, vault_token, namespace, mount_path, 
                    engine_type, engine_version, is_active, created_by) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [config_name, vault_address, vault_token, namespace, mount_path, 
                 engine_type, engine_version, is_active, created_by]
            )
            return result.last_insert_id
        except Exception as e:
            logger.error(f"Error creating vault config: {e}")
            return None
    
    @staticmethod
    async def get_by_id(config_id: int) -> Optional[Dict]:
        """Get vault configuration by ID."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                """SELECT id, config_name, vault_address, vault_token, namespace, 
                          mount_path, engine_type, engine_version, is_active, 
                          created_by, created_at, updated_at 
                   FROM vault_configs WHERE id = ?""",
                [config_id]
            )
            
            if result.rows:
                row = result.rows[0]
                return {
                    "id": row[0],
                    "config_name": row[1],
                    "vault_address": row[2],
                    "vault_token": row[3],
                    "namespace": row[4],
                    "mount_path": row[5],
                    "engine_type": row[6],
                    "engine_version": row[7],
                    "is_active": bool(row[8]),
                    "created_by": row[9],
                    "created_at": row[10],
                    "updated_at": row[11]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting vault config by ID: {e}")
            return None
    
    @staticmethod
    async def get_by_name(config_name: str) -> Optional[Dict]:
        """Get vault configuration by name."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                """SELECT id, config_name, vault_address, vault_token, namespace, 
                          mount_path, engine_type, engine_version, is_active, 
                          created_by, created_at, updated_at 
                   FROM vault_configs WHERE config_name = ?""",
                [config_name]
            )
            
            if result.rows:
                row = result.rows[0]
                return {
                    "id": row[0],
                    "config_name": row[1],
                    "vault_address": row[2],
                    "vault_token": row[3],
                    "namespace": row[4],
                    "mount_path": row[5],
                    "engine_type": row[6],
                    "engine_version": row[7],
                    "is_active": bool(row[8]),
                    "created_by": row[9],
                    "created_at": row[10],
                    "updated_at": row[11]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting vault config by name: {e}")
            return None
    
    @staticmethod
    async def get_all(
        engine_type: str = None,
        is_active: bool = None,
        created_by: str = None
    ) -> List[Dict]:
        """Get all vault configurations with optional filtering."""
        if not db_service.client:
            return []
        try:
            query = """SELECT id, config_name, vault_address, vault_token, namespace, 
                              mount_path, engine_type, engine_version, is_active, 
                              created_by, created_at, updated_at 
                       FROM vault_configs"""
            params = []
            
            if engine_type or is_active is not None or created_by:
                query += " WHERE"
                conditions = []
                
                if engine_type:
                    conditions.append("engine_type = ?")
                    params.append(engine_type)
                
                if is_active is not None:
                    conditions.append("is_active = ?")
                    params.append(is_active)
                
                if created_by:
                    conditions.append("created_by = ?")
                    params.append(created_by)
                
                query += " " + " AND ".join(conditions)
            
            query += " ORDER BY config_name, created_at DESC"
            
            result = await db_service.client.execute(query, params)
            
            configs = []
            for row in result.rows:
                configs.append({
                    "id": row[0],
                    "config_name": row[1],
                    "vault_address": row[2],
                    "vault_token": row[3],
                    "namespace": row[4],
                    "mount_path": row[5],
                    "engine_type": row[6],
                    "engine_version": row[7],
                    "is_active": bool(row[8]),
                    "created_by": row[9],
                    "created_at": row[10],
                    "updated_at": row[11]
                })
            
            return configs
        except Exception as e:
            logger.error(f"Error getting all vault configs: {e}")
            return []
    
    @staticmethod
    async def update(config_id: int, **kwargs) -> bool:
        """Update a vault configuration."""
        if not db_service.client:
            return False
        try:
            updates = []
            params = []
            
            for key, value in kwargs.items():
                if key in ["config_name", "vault_address", "vault_token", "namespace", 
                          "mount_path", "engine_type", "engine_version", "is_active"]:
                    updates.append(f"{key} = ?")
                    params.append(value)
            
            if not updates:
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(config_id)
            
            query = f"UPDATE vault_configs SET {', '.join(updates)} WHERE id = ?"
            result = await db_service.client.execute(query, params)
            
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error updating vault config: {e}")
            return False
    
    @staticmethod
    async def delete(config_id: int) -> bool:
        """Delete a vault configuration."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "DELETE FROM vault_configs WHERE id = ?",
                [config_id]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting vault config: {e}")
            return False
    
    @staticmethod
    async def get_active_configs() -> List[Dict]:
        """Get all active vault configurations."""
        return await VaultConfigRepository.get_all(is_active=True)