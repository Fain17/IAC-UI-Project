import libsql_client
from libsql_client import create_client, Client
from app.config import LIBSQL_URL, LIBSQL_AUTH_TOKEN
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    user_id INTEGER NOT NULL,
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
                    user_id INTEGER NOT NULL,
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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    user_id INTEGER UNIQUE NOT NULL,
                    permission_level TEXT NOT NULL,  -- admin, manager, viewer
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Create user group assignments table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS user_group_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    group_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (group_id) REFERENCES user_groups (id),
                    UNIQUE(user_id, group_id)
                )
            """)
            
            # Check if workflows table exists and migrate if needed
            await self._migrate_workflows_table()
            
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
            """)
            
            if not result.rows:
                # Table doesn't exist, create it with UUID support
                await self.client.execute("""
                    CREATE TABLE workflows (
                        id TEXT PRIMARY KEY,  -- UUID for workflow
                        user_id INTEGER NOT NULL,
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
                        user_id INTEGER NOT NULL,
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
    
    async def close(self):
        """Close database connection."""
        if self.client:
            await self.client.close()
            logger.info("Database connection closed")

# Global database service instance
db_service = DatabaseService() 