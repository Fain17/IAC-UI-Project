from typing import List, Optional, Dict
from app.db.database import db_service
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
    async def get_by_id(user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "SELECT id, username, email, is_active, is_admin FROM users WHERE id = ? AND is_active = TRUE",
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
    async def create(username: str, email: str, hashed_password: str, is_admin: bool = False) -> bool:
        """Create a new user."""
        if not db_service.client:
            return False
        try:
            # Check if user already exists
            result = await db_service.client.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?",
                [username, email]
            )
            
            if result.rows:
                return False
            
            # Create new user
            await db_service.client.execute(
                "INSERT INTO users (username, email, hashed_password, is_admin) VALUES (?, ?, ?, ?)",
                [username, email, hashed_password, is_admin]
            )
            return True
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
    
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
    async def delete(user_id: int) -> bool:
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
    async def update_is_active(user_id: int, is_active: bool) -> bool:
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

class UserSessionRepository:
    """Repository for user session operations."""
    @staticmethod
    async def create(user_id: int, session_token: str, expires_at):
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

class RefreshTokenRepository:
    """Repository for refresh token operations."""
    
    @staticmethod
    async def create(user_id: int, refresh_token: str, expires_at) -> bool:
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
    async def revoke_all_for_user(user_id: int) -> bool:
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

class WorkflowRepository:
    """Repository for workflow operations."""
    
    @staticmethod
    async def create(user_id: int, name: str, description: str, steps: list, script_type: str = None, script_content: str = None, script_filename: str = None, run_command: str = None, dependencies: list = None, is_active: bool = True) -> Optional[int]:
        """Create a new workflow and return its ID."""
        if not db_service.client:
            return None
        try:
            steps_json = json.dumps(steps)
            dependencies_json = json.dumps(dependencies) if dependencies else None
            
            result = await db_service.client.execute(
                "INSERT INTO workflows (user_id, name, description, steps, script_type, script_content, script_filename, run_command, dependencies, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
                [user_id, name, description, steps_json, script_type, script_content, script_filename, run_command, dependencies_json, is_active]
            )
            
            # Check if the insert actually worked
            if not result.rows:
                return None
            
            workflow_id = result.rows[0][0]
            return workflow_id
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            return None
    
    @staticmethod
    async def get_by_id(workflow_id: int, user_id: int) -> Optional[Dict]:
        """Get workflow by ID for a specific user."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "SELECT id, name, description, steps, script_type, script_content, script_filename, run_command, dependencies, is_active, created_at, updated_at FROM workflows WHERE id = ? AND user_id = ?",
                [workflow_id, user_id]
            )
            
            if not result.rows:
                return None
            
            workflow = result.rows[0]
            return {
                "id": workflow[0],
                "name": workflow[1],
                "description": workflow[2],
                "steps": json.loads(workflow[3]),
                "script_type": workflow[4],
                "script_content": workflow[5],
                "script_filename": workflow[6],
                "run_command": workflow[7],
                "dependencies": json.loads(workflow[8]) if workflow[8] else None,
                "is_active": bool(workflow[9]),
                "created_at": workflow[10],
                "updated_at": workflow[11]
            }
        except Exception as e:
            logger.error(f"Error getting workflow by ID: {e}")
            return None
    
    @staticmethod
    async def get_all_by_user(user_id: int) -> List[Dict]:
        """Get all workflows for a specific user."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute(
                "SELECT id, name, description, steps, script_type, script_content, script_filename, run_command, dependencies, is_active, created_at, updated_at FROM workflows WHERE user_id = ? ORDER BY created_at DESC",
                [user_id]
            )
            
            workflows = []
            for row in result.rows:
                workflows.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "steps": json.loads(row[3]),
                    "script_type": row[4],
                    "script_content": row[5],
                    "script_filename": row[6],
                    "run_command": row[7],
                    "dependencies": json.loads(row[8]) if row[8] else None,
                    "is_active": bool(row[9]),
                    "created_at": row[10],
                    "updated_at": row[11]
                })
            return workflows
        except Exception as e:
            logger.error(f"Error getting workflows for user: {e}")
            return []
    
    @staticmethod
    async def delete(workflow_id: int, user_id: int) -> bool:
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
    async def update(workflow_id: int, user_id: int, name: str = None, description: str = None, steps: list = None, script_type: str = None, script_content: str = None, script_filename: str = None, run_command: str = None, dependencies: list = None, is_active: bool = None) -> bool:
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
            if script_type is not None:
                updates.append("script_type = ?")
                params.append(script_type)
            if script_content is not None:
                updates.append("script_content = ?")
                params.append(script_content)
            if script_filename is not None:
                updates.append("script_filename = ?")
                params.append(script_filename)
            if run_command is not None:
                updates.append("run_command = ?")
                params.append(run_command)
            if dependencies is not None:
                updates.append("dependencies = ?")
                params.append(json.dumps(dependencies))
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

class ScriptExecutionRepository:
    """Repository for script execution tracking."""
    
    @staticmethod
    async def create_execution(execution_id: str, workflow_id: int, user_id: int, parameters: dict = None, environment: dict = None) -> bool:
        """Create a new script execution record."""
        if not db_service.client:
            return False
        try:
            parameters_json = json.dumps(parameters) if parameters else None
            environment_json = json.dumps(environment) if environment else None
            
            await db_service.client.execute(
                "INSERT INTO script_executions (execution_id, workflow_id, user_id, status, parameters, environment) VALUES (?, ?, ?, ?, ?, ?)",
                [execution_id, workflow_id, user_id, "running", parameters_json, environment_json]
            )
            return True
        except Exception as e:
            logger.error(f"Error creating script execution: {e}")
            return False
    
    @staticmethod
    async def update_execution_result(execution_id: str, status: str, output: str = None, error: str = None, exit_code: int = None, execution_time: float = None) -> bool:
        """Update script execution with results."""
        if not db_service.client:
            return False
        try:
            await db_service.client.execute(
                "UPDATE script_executions SET status = ?, output = ?, error = ?, exit_code = ?, execution_time = ?, completed_at = CURRENT_TIMESTAMP WHERE execution_id = ?",
                [status, output, error, exit_code, execution_time, execution_id]
            )
            return True
        except Exception as e:
            logger.error(f"Error updating script execution: {e}")
            return False
    
    @staticmethod
    async def get_execution(execution_id: str) -> Optional[Dict]:
        """Get script execution by ID."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "SELECT execution_id, workflow_id, user_id, status, output, error, exit_code, execution_time, parameters, environment, started_at, completed_at FROM script_executions WHERE execution_id = ?",
                [execution_id]
            )
            
            if not result.rows:
                return None
            
            execution = result.rows[0]
            return {
                "execution_id": execution[0],
                "workflow_id": execution[1],
                "user_id": execution[2],
                "status": execution[3],
                "output": execution[4],
                "error": execution[5],
                "exit_code": execution[6],
                "execution_time": execution[7],
                "parameters": json.loads(execution[8]) if execution[8] else None,
                "environment": json.loads(execution[9]) if execution[9] else None,
                "started_at": execution[10],
                "completed_at": execution[11]
            }
        except Exception as e:
            logger.error(f"Error getting script execution: {e}")
            return None
    
    @staticmethod
    async def get_executions_by_workflow(workflow_id: int, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recent executions for a workflow."""
        if not db_service.client:
            return []
        try:
            result = await db_service.client.execute(
                "SELECT execution_id, status, output, error, exit_code, execution_time, started_at, completed_at FROM script_executions WHERE workflow_id = ? AND user_id = ? ORDER BY started_at DESC LIMIT ?",
                [workflow_id, user_id, limit]
            )
            
            executions = []
            for row in result.rows:
                executions.append({
                    "execution_id": row[0],
                    "status": row[1],
                    "output": row[2],
                    "error": row[3],
                    "exit_code": row[4],
                    "execution_time": row[5],
                    "started_at": row[6],
                    "completed_at": row[7]
                })
            return executions
        except Exception as e:
            logger.error(f"Error getting workflow executions: {e}")
            return []

class UserGroupRepository:
    """Repository for user group operations."""
    
    @staticmethod
    async def create(name: str, description: str = None) -> Optional[int]:
        """Create a new user group and return its ID."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "INSERT INTO user_groups (name, description) VALUES (?, ?) RETURNING id",
                [name, description]
            )
            return result.rows[0][0] if result.rows else None
        except Exception as e:
            logger.error(f"Error creating user group: {e}")
            return None
    
    @staticmethod
    async def get_by_id(group_id: int) -> Optional[Dict]:
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
    async def update(group_id: int, name: str = None, description: str = None) -> bool:
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
    async def delete(group_id: int) -> bool:
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
    async def create(user_id: int, permission_level: str) -> Optional[int]:
        """Create a new user permission and return its ID."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "INSERT INTO user_permissions (user_id, permission_level) VALUES (?, ?) RETURNING id",
                [user_id, permission_level]
            )
            return result.rows[0][0] if result.rows else None
        except Exception as e:
            logger.error(f"Error creating user permission: {e}")
            return None
    
    @staticmethod
    async def get_by_user_id(user_id: int) -> Optional[Dict]:
        """Get user permission by user ID."""
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "SELECT id, user_id, permission_level, created_at, updated_at FROM user_permissions WHERE user_id = ?",
                [user_id]
            )
            
            if not result.rows:
                return None
            
            permission = result.rows[0]
            return {
                "id": permission[0],
                "user_id": permission[1],
                "permission_level": permission[2],
                "created_at": permission[3],
                "updated_at": permission[4]
            }
        except Exception as e:
            logger.error(f"Error getting user permission: {e}")
            return None
    
    @staticmethod
    async def update(user_id: int, permission_level: str) -> bool:
        """Update user permission."""
        if not db_service.client:
            return False
        try:
            result = await db_service.client.execute(
                "UPDATE user_permissions SET permission_level = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                [permission_level, user_id]
            )
            return result.rows_affected > 0
        except Exception as e:
            logger.error(f"Error updating user permission: {e}")
            return False
    
    @staticmethod
    async def delete(user_id: int) -> bool:
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

class UserGroupAssignmentRepository:
    """Repository for user group assignment operations."""
    
    @staticmethod
    async def create(user_id: int, group_id: int) -> Optional[int]:
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
    async def get_user_groups(user_id: int) -> List[Dict]:
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
    async def get_group_users(group_id: int) -> List[Dict]:
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
    async def remove_user_from_group(user_id: int, group_id: int) -> bool:
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