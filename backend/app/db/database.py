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
            
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    async def close(self):
        """Close database connection."""
        if self.client:
            await self.client.close()

# Global database service instance
db_service = DatabaseService() 