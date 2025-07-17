from typing import List, Optional, Dict
from app.db.database import db_service
from app.db.models import ConfigMapping, User, UserCreate, ConfigMappingCreate
import logging

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
                "SELECT id, username, email, is_active FROM users WHERE id = ? AND is_active = TRUE",
                [user_id]
            )
            
            if not result.rows:
                return None
            
            user = result.rows[0]
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "is_active": user[3]
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
                "SELECT id, username, email, hashed_password, is_active FROM users WHERE username = ? AND is_active = TRUE",
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
                "is_active": user[4]
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
                "SELECT id, username, email, hashed_password, is_active FROM users WHERE email = ? AND is_active = TRUE",
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
                "is_active": user[4]
            }
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    @staticmethod
    async def create(username: str, email: str, hashed_password: str) -> bool:
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
                "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
                [username, email, hashed_password]
            )
            return True
        except Exception as e:
            logger.error(f"Error creating user: {e}")
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