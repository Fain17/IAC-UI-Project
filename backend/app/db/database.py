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
            
            logger.info("Database tables created successfully")
            
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
    
    async def close(self):
        """Close database connection."""
        if self.client:
            await self.client.close()
            logger.info("Database connection closed")

# Global database service instance
db_service = DatabaseService() 