import libsql_client
from libsql_client import create_client, Client
from app.config import LIBSQL_URL, LIBSQL_AUTH_TOKEN
from typing import Optional, List, Dict, Any
import logging
import sqlite3
import asyncio
import logging
import json
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

def generate_user_id() -> str:
    """Generate a unique user ID."""
    return f"user_{uuid.uuid4().hex[:8]}"

def generate_group_id() -> str:
    """Generate a unique group ID."""
    return f"group_{uuid.uuid4().hex[:8]}"

class DatabaseService:
    def __init__(self):
        self.client: Optional[Client] = None
    
    async def initialize(self):
        """Async initialization."""
        await self._connect()
        await self._create_tables()
    
    async def _connect(self):
        """Initialize database connection."""
        try:
            if LIBSQL_AUTH_TOKEN:
                self.client = create_client(
                    url=LIBSQL_URL,
                    auth_token=LIBSQL_AUTH_TOKEN
                )
            else:
                self.client = create_client(url=LIBSQL_URL)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def _create_tables(self):
        """Create necessary tables if they don't exist."""
        if not self.client:
            raise RuntimeError("Database client not initialized")
            
        try:
            # Create config mappings table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS config_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instance_name TEXT UNIQUE NOT NULL,
                    launch_template_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create users table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create user sessions table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Create refresh tokens table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    refresh_token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    is_revoked BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Create user groups table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS user_groups (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create user permissions table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS user_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,  -- admin, manager, viewer
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Create role permissions table for predefined roles
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS role_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,  -- admin, manager, viewer
                    permission TEXT NOT NULL,  -- read, write, delete, execute
                    resource_type TEXT NOT NULL,  -- workflow, user, group, system, etc.
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(role, permission, resource_type)
                )
            """)
            
            # Create granular user permissions table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS user_permissions_granular (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    permission TEXT NOT NULL,  -- read, write, execute, delete
                    resource_type TEXT NOT NULL,  -- workflow, user, group, etc.
                    resource_id TEXT,  -- specific resource ID, null for global permissions
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, permission, resource_type, resource_id)
                )
            """)
            
            # Create user group assignments table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS user_group_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    group_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (group_id) REFERENCES user_groups (id),
                    UNIQUE(user_id, group_id)
                )
            """)
            
            # Check if workflows table exists and migrate if needed
            await self._migrate_workflows_table()
            
            # Check if user_permissions table needs migration
            await self._migrate_user_permissions_table()
            
            # Check if users and groups tables need migration
            await self._migrate_users_and_groups_tables()
            
            # Create docker image mappings table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS docker_image_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    types TEXT NOT NULL, -- JSON array of script types (e.g., ["python"], ["python","nodejs"]) 
                    image TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create workflow shares table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS workflow_shares (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    group_id TEXT NOT NULL,
                    permission TEXT DEFAULT 'read', -- read|write|execute (reserved)
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(workflow_id, group_id),
                    FOREIGN KEY (workflow_id) REFERENCES workflows(id),
                    FOREIGN KEY (group_id) REFERENCES user_groups(id)
                )
            """)
            
            # Create docker execution mappings table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS docker_mappings (
                    id TEXT PRIMARY KEY,  -- UUID for mapping
                    script_type TEXT NOT NULL,  -- python, nodejs, bash, etc.
                    docker_image TEXT NOT NULL,  -- custom-python:3.9
                    docker_tag TEXT DEFAULT 'latest',
                    description TEXT,
                    environment_variables TEXT,  -- JSON object
                    volumes TEXT,  -- JSON array of volume mounts
                    ports TEXT,  -- JSON array of port mappings
                    is_active BOOLEAN DEFAULT TRUE,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """)
            
            # Create custom resource mappings table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS resource_mappings (
                    id TEXT PRIMARY KEY,  -- UUID for mapping
                    mapping_type TEXT NOT NULL,  -- ec2_to_lt, ec2_to_ami, etc.
                    source_resource TEXT NOT NULL,  -- i-1234567890abcdef0
                    target_resource TEXT NOT NULL,  -- lt-0987654321fedcba0
                    description TEXT,
                    metadata TEXT,  -- JSON object for additional data
                    is_active BOOLEAN DEFAULT TRUE,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """)
            
            # Create HashiCorp Vault configurations table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS vault_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name TEXT UNIQUE NOT NULL,
                    vault_address TEXT NOT NULL,
                    vault_token TEXT NOT NULL,
                    namespace TEXT,
                    mount_path TEXT NOT NULL,
                    engine_type TEXT NOT NULL,
                    engine_version TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """)
            
            # Create workflow schedules table
            # Note: This is now handled in _migrate_workflow_schedules_table()
            
            # Migrate workflow_schedules table if needed
            await self._migrate_workflow_schedules_table()
            
            logger.info("Database tables created successfully")
            
            # Initialize default role permissions
            await self._initialize_default_role_permissions()
            
            # Ensure admin permissions are always maintained
            await self._ensure_admin_permissions_always_exist()
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    async def _migrate_workflows_table(self):
        """Migrate workflows table to support UUIDs if needed."""
        try:
            # Check if workflows table exists
            result = await self.client.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='workflows'
            """
            )
            
            if not result.rows:
                # Table doesn't exist, create it with UUID support
                await self.client.execute("""
                    CREATE TABLE workflows (
                        id TEXT PRIMARY KEY,  -- UUID for workflow
                        user_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        steps TEXT NOT NULL,  -- JSON string of workflow steps
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                logger.info("Created workflows table with UUID support")
                return
            
            # Table exists, check if it needs migration
            result = await self.client.execute("PRAGMA table_info(workflows)")
            columns = {row[1]: row[2] for row in result.rows}
            
            if 'id' in columns and columns['id'] == 'INTEGER':
                # Need to migrate from INTEGER to TEXT
                logger.info("Migrating workflows table from INTEGER to UUID support...")
                
                # Create new table with UUID support
                await self.client.execute("""
                    CREATE TABLE workflows_new (
                        id TEXT PRIMARY KEY,  -- UUID for workflow
                        user_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        steps TEXT NOT NULL,  -- JSON string of workflow steps
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                # Copy existing data with UUID conversion
                await self.client.execute("""
                    INSERT INTO workflows_new (id, user_id, name, description, steps, is_active, created_at, updated_at)
                    SELECT 
                        'migrated_' || CAST(id AS TEXT) || '_' || CAST(strftime('%s', 'now') AS TEXT) as id,
                        user_id,
                        name,
                        description,
                        steps,
                        is_active,
                        created_at,
                        updated_at
                    FROM workflows
                """)
                
                # Drop old table and rename new one
                await self.client.execute("DROP TABLE workflows")
                await self.client.execute("ALTER TABLE workflows_new RENAME TO workflows")
                
                logger.info("Successfully migrated workflows table to UUID support")
            else:
                logger.info("Workflows table already supports UUIDs")
                
        except Exception as e:
            logger.error(f"Error migrating workflows table: {e}")
            raise
    
    async def _migrate_user_permissions_table(self):
        """Migrate user_permissions table from permission_level to role column."""
        try:
            # Check if user_permissions table exists
            result = await self.client.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='user_permissions'
            """
            )
            
            if not result.rows:
                logger.info("user_permissions table does not exist, no migration needed.")
                return
            
            # Check if 'permission_level' column exists
            result = await self.client.execute("PRAGMA table_info(user_permissions)")
            columns = {row[1]: row[2] for row in result.rows}
            
            if 'permission_level' in columns:
                logger.info("Migrating user_permissions table from permission_level to role column...")
                
                # Create new table with 'role' column
                await self.client.execute("""
                    CREATE TABLE user_permissions_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER UNIQUE NOT NULL,
                        role TEXT NOT NULL,  -- admin, manager, viewer
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                # Copy existing data, converting permission_level to role
                await self.client.execute("""
                    INSERT INTO user_permissions_new (user_id, role, created_at, updated_at)
                    SELECT 
                        user_id, 
                        CASE 
                            WHEN permission_level = 'admin' THEN 'admin'
                            WHEN permission_level = 'manager' THEN 'manager'
                            ELSE 'viewer'
                        END as role,
                        created_at, 
                        updated_at 
                    FROM user_permissions
                """)
                
                # Drop old table and rename new one
                await self.client.execute("DROP TABLE user_permissions")
                await self.client.execute("ALTER TABLE user_permissions_new RENAME TO user_permissions")
                
                logger.info("Successfully migrated user_permissions table to role column")
            else:
                logger.info("user_permissions table already has 'role' column, no migration needed.")
                
        except Exception as e:
            logger.error(f"Error migrating user_permissions table: {e}")
            raise
    
    async def _migrate_users_and_groups_tables(self):
        """Migrate users and user_groups tables to support UUIDs if needed."""
        try:
            # Check if users table exists
            result = await self.client.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='users'
            """
            )
            
            if not result.rows:
                logger.info("users table does not exist, no migration needed.")
                return
            
            # Check if 'id' column is INTEGER
            result = await self.client.execute("PRAGMA table_info(users)")
            columns = {row[1]: row[2] for row in result.rows}
            
            if 'id' in columns and columns['id'] == 'INTEGER':
                logger.info("Migrating users table from INTEGER to UUID support...")
                
                # Create new table with UUID support
                await self.client.execute("""
                    CREATE TABLE users_new (
                        id TEXT PRIMARY KEY,  -- UUID for user
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        hashed_password TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        is_admin BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Copy existing data with UUID conversion
                await self.client.execute("""
                    INSERT INTO users_new (id, username, email, hashed_password, is_active, is_admin, created_at, updated_at)
                    SELECT 
                        'migrated_' || CAST(id AS TEXT) || '_' || CAST(strftime('%s', 'now') AS TEXT) as id,
                        username,
                        email,
                        hashed_password,
                        is_active,
                        is_admin,
                        created_at,
                        updated_at
                    FROM users
                """)
                
                # Drop old table and rename new one
                await self.client.execute("DROP TABLE users")
                await self.client.execute("ALTER TABLE users_new RENAME TO users")
                
                logger.info("Successfully migrated users table to UUID support")
            else:
                logger.info("users table already supports UUIDs")
                
            # Check if user_groups table exists
            result = await self.client.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='user_groups'
            """
            )
            
            if not result.rows:
                logger.info("user_groups table does not exist, no migration needed.")
                return
            
            # Check if 'id' column is INTEGER
            result = await self.client.execute("PRAGMA table_info(user_groups)")
            columns = {row[1]: row[2] for row in result.rows}
            
            if 'id' in columns and columns['id'] == 'INTEGER':
                logger.info("Migrating user_groups table from INTEGER to UUID support...")
                
                # Create new table with UUID support
                await self.client.execute("""
                    CREATE TABLE user_groups_new (
                        id TEXT PRIMARY KEY,  -- UUID for group
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Copy existing data with proper UUID conversion
                # Get all existing groups first
                existing_groups = await self.client.execute("SELECT id, name, description, created_at, updated_at FROM user_groups")
                
                for group in existing_groups.rows:
                    old_id, name, description, created_at, updated_at = group
                    # Generate proper UUID for each group
                    new_id = generate_group_id()
                    
                    await self.client.execute("""
                        INSERT INTO user_groups_new (id, name, description, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, [new_id, name, description, created_at, updated_at])
                    
                    # Update references in other tables
                    try:
                        await self.client.execute("UPDATE user_group_assignments SET group_id = ? WHERE group_id = ?", [new_id, old_id])
                    except:
                        pass  # Table might not exist yet
                    
                    try:
                        await self.client.execute("UPDATE workflow_shares SET group_id = ? WHERE group_id = ?", [new_id, old_id])
                    except:
                        pass  # Table might not exist yet
                
                # Drop old table and rename new one
                await self.client.execute("DROP TABLE user_groups")
                await self.client.execute("ALTER TABLE user_groups_new RENAME TO user_groups")
                
                logger.info("Successfully migrated user_groups table to UUID support")
            else:
                logger.info("user_groups table already supports UUIDs")
                
        except Exception as e:
            logger.error(f"Error migrating users and groups tables: {e}")
            raise
    
    async def _migrate_workflow_schedules_table(self):
        """Migrate workflow_schedules table to new schema with UUID support."""
        try:
            # Check if workflow_schedules table exists
            result = await self.client.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='workflow_schedules'
            """)
            
            if result.rows:
                logger.info("Dropping existing workflow_schedules table to update schema with UUID support...")
                await self.client.execute("DROP TABLE workflow_schedules")
            
            # Create new table with UUID support
            await self.client.execute("""
                CREATE TABLE workflow_schedules (
                    id TEXT PRIMARY KEY,  -- UUID for schedule
                    workflow_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    schedule_type TEXT NOT NULL, -- interval, daily, weekly, monthly
                    schedule_value TEXT NOT NULL, -- e.g., "30m", "09:00", "monday:09:00", "15:09:00"
                    description TEXT, -- optional description of the schedule
                    is_active BOOLEAN DEFAULT TRUE, -- whether the schedule is active
                    continue_on_failure BOOLEAN DEFAULT TRUE, -- continue execution on step failure
                    last_execution TIMESTAMP, -- when the schedule last executed
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_id) REFERENCES workflows(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            logger.info("Successfully created workflow_schedules table with UUID support")
            
        except Exception as e:
            logger.error(f"Error migrating workflow_schedules table: {e}")
            raise
    
    async def _initialize_default_role_permissions(self):
        """Initialize default permissions for predefined roles."""
        if not self.client:
            return
            
        try:
            # For a new feature, we'll just recreate the table to ensure correct structure
            # Drop the table if it exists to ensure clean slate
            await self.client.execute("DROP TABLE IF EXISTS role_permissions")
            
            # Create the table with correct structure
            await self.client.execute("""
                CREATE TABLE role_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,  -- admin, manager, viewer
                    permission TEXT NOT NULL,  -- read, write, delete, execute
                    resource_type TEXT NOT NULL,  -- workflow, user, group, system, etc.
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(role, permission, resource_type)
                )
            """)
            
            # Default permissions for Admin role (all permissions)
            admin_permissions = [
                ("admin", "read", "workflow"),
                ("admin", "write", "workflow"),
                ("admin", "delete", "workflow"),
                ("admin", "execute", "workflow"),
                ("admin", "read", "user"),
                ("admin", "write", "user"),
                ("admin", "delete", "user"),
                ("admin", "execute", "user"),
                ("admin", "read", "group"),
                ("admin", "write", "group"),
                ("admin", "delete", "group"),
                ("admin", "execute", "group"),
                ("admin", "read", "system"),
                ("admin", "write", "system"),
                ("admin", "delete", "system"),
                ("admin", "execute", "system"),
            ]
            
            # Default permissions for Manager role
            manager_permissions = [
                ("manager", "read", "workflow"),
                ("manager", "write", "workflow"),
                ("manager", "execute", "workflow"),
                ("manager", "read", "user"),
                ("manager", "read", "group"),
                ("manager", "write", "group"),
                ("manager", "read", "system"),
            ]
            
            # Default permissions for Viewer role
            viewer_permissions = [
                ("viewer", "read", "workflow"),
                ("viewer", "read", "user"),
                ("viewer", "read", "group"),
                ("viewer", "read", "system"),
            ]
            
            # Insert all permissions
            all_permissions = admin_permissions + manager_permissions + viewer_permissions
            
            for role, permission, resource_type in all_permissions:
                await self.client.execute("""
                    INSERT INTO role_permissions (role, permission, resource_type)
                    VALUES (?, ?, ?)
                """, [role, permission, resource_type])
            
            logger.info(f"Initialized {len(all_permissions)} default role permissions")
            
        except Exception as e:
            logger.error(f"Error initializing default role permissions: {e}")
            # Don't raise here as this is not critical for database operation
    
    async def _ensure_admin_permissions_always_exist(self):
        """Ensures that the 'admin' role always has all permissions."""
        if not self.client:
            return
            
        try:
            # Since we recreate the table every time in _initialize_default_role_permissions,
            # this method is no longer needed for the basic functionality
            # But we'll keep it as a safety check for any future manual modifications
            result = await self.client.execute("""
                SELECT COUNT(*) FROM role_permissions 
                WHERE role = 'admin'
            """)
            
            admin_permission_count = result.rows[0][0]
            expected_admin_permissions = 16  # 4 permissions × 4 resource types
            
            if admin_permission_count < expected_admin_permissions:
                logger.warning(f"Admin role has {admin_permission_count} permissions, expected {expected_admin_permissions}")
                # Re-run initialization to fix any missing permissions
                await self._initialize_default_role_permissions()
            else:
                logger.info(f"Admin role has all {admin_permission_count} expected permissions")
            
        except Exception as e:
            logger.error(f"Error ensuring admin permissions: {e}")
            # Don't raise here as this is not critical for database operation
    
    async def reset_all_role_permissions(self):
        """Reset all role permissions to their default values."""
        if not self.client:
            return False
            
        try:
            logger.info("Resetting all role permissions to defaults...")
            await self._initialize_default_role_permissions()
            logger.info("Successfully reset all role permissions to defaults")
            return True
        except Exception as e:
            logger.error(f"Error resetting all role permissions: {e}")
            return False
    
    async def close(self):
        """Close database connection."""
        if self.client:
            await self.client.close()
            logger.info("Database connection closed")

# Global database service instance
db_service = DatabaseService() 