from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.db.repositories import UserRepository, UserSessionRepository
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = REFRESH_TOKEN_EXPIRE_DAYS
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    async def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token and store session."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        # Store session in DB
        user_id = data.get("sub")
        if user_id:
            # Store session with expiry in ISO format
            try:
                # Convert to ISO format for consistent storage
                expire_iso = expire.isoformat()
                success = await UserSessionRepository.create(user_id, encoded_jwt, expire_iso)
                if success:
                    logger.info(f"Session created successfully for user {user_id}, expires at {expire_iso}")
                else:
                    logger.error(f"Failed to create session for user {user_id}")
            except Exception as e:
                logger.error(f"Error creating session: {e}")
        return encoded_jwt

    async def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT refresh token and store in database."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            # Refresh tokens last configurable days by default
            # For testing: convert days to minutes if less than 1 day
            if self.refresh_token_expire_days < 1:
                # Convert to minutes for short durations
                minutes = int(self.refresh_token_expire_days * 24 * 60)
                expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
            else:
                expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({"exp": expire, "type": "refresh"})  # Add type to distinguish from access tokens
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        # Store refresh token in database
        user_id = data.get("sub")
        if user_id:
            from app.db.repositories import RefreshTokenRepository
            try:
                expire_iso = expire.isoformat()
                success = await RefreshTokenRepository.create(user_id, encoded_jwt, expire_iso)
                if success:
                    logger.info(f"Refresh token created successfully for user {user_id}, expires at {expire_iso}")
                else:
                    logger.error(f"Failed to create refresh token for user {user_id}")
            except Exception as e:
                logger.error(f"Error creating refresh token: {e}")
        
        return encoded_jwt

    async def verify_refresh_token(self, refresh_token: str) -> Optional[dict]:
        """Verify and decode a refresh token, check database validity."""
        try:
            # Decode JWT token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if it's actually a refresh token
            if payload.get("type") != "refresh":
                logger.warning("Token is not a refresh token")
                return None
            
            # Check database for token validity
            from app.db.repositories import RefreshTokenRepository
            token_info = await RefreshTokenRepository.get_by_token(refresh_token)
            
            if not token_info:
                logger.warning("Refresh token not found in database")
                return None
            
            # Check if token is revoked
            if token_info["is_revoked"]:
                logger.warning("Refresh token is revoked")
                return None
            
            # Check expiration
            expires_at_str = token_info["expires_at"]
            current_time = datetime.now(timezone.utc)
            
            try:
                if isinstance(expires_at_str, str):
                    if 'T' in expires_at_str:
                        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                    else:
                        expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                elif isinstance(expires_at_str, (int, float)):
                    # Handle timestamp as Unix timestamp
                    expires_at = datetime.fromtimestamp(expires_at_str, tz=timezone.utc)
                elif isinstance(expires_at_str, datetime):
                    # Already a datetime object
                    expires_at = expires_at_str
                else:
                    logger.error(f"Unknown refresh token expires_at type: {type(expires_at_str)}")
                    return None
                
                if current_time > expires_at:
                    logger.warning("Refresh token has expired")
                    # Clean up expired token
                    await RefreshTokenRepository.delete_by_token(refresh_token)
                    return None
                    
            except Exception as e:
                logger.error(f"Error parsing refresh token expiration: {e}")
                return None
            
            return payload
            
        except JWTError as e:
            logger.warning(f"Invalid refresh token JWT: {e}")
            return None

    async def refresh_access_token(self, refresh_token: str) -> Optional[dict]:
        """Use refresh token to get new access token (keep same refresh token)."""
        # Verify refresh token
        payload = await self.verify_refresh_token(refresh_token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Get user info
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Check if user is active
        if not user.get("is_active", True):
            logger.warning(f"Refresh token attempt for inactive user {user_id}")
            return None
        
        # Create new access token (short-lived)
        new_access_token = await self.create_access_token(
            data={"sub": str(user_id)},
            expires_delta=timedelta(minutes=self.access_token_expire_minutes)
        )
        
        # Keep the same refresh token (no token rotation)
        # This allows the same refresh token to be used multiple times
        # until it expires naturally
        
        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,  # Return the same refresh token
            "token_type": "bearer",
            "user": user
        }
    
    async def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode a JWT token, and check session table."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            # Check session table for token existence and expiration
            from app.db.database import db_service
            if not db_service.client:
                return None
            
            result = await db_service.client.execute(
                "SELECT expires_at FROM user_sessions WHERE session_token = ?",
                [token]
            )
            
            if not result.rows:
                return None
            
            expires_at_str = result.rows[0][0]
            current_time = datetime.now(timezone.utc)
            
            # Parse the expiration timestamp
            try:
                if isinstance(expires_at_str, str):
                    if 'T' in expires_at_str:
                        # ISO format
                        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                    else:
                        # SQLite format: "2025-07-29 11:53:59"
                        expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                elif isinstance(expires_at_str, (int, float)):
                    # Handle timestamp as Unix timestamp
                    expires_at = datetime.fromtimestamp(expires_at_str, tz=timezone.utc)
                elif isinstance(expires_at_str, datetime):
                    # Already a datetime object
                    expires_at = expires_at_str
                else:
                    logger.error(f"Unknown expires_at type: {type(expires_at_str)}")
                    return None
                
                if current_time > expires_at:
                    # Session expired, clean it up immediately
                    logger.info(f"Session expired, cleaning up token: {token[:20]}...")
                    await UserSessionRepository.delete_by_token(token)
                    return None
                    
            except Exception as e:
                logger.error(f"Error parsing session expiration: {e}")
                return None
                
            return payload
        except JWTError:
            return None
    
    async def logout(self, token: str) -> bool:
        from app.db.repositories import UserSessionRepository
        return await UserSessionRepository.delete_by_token(token)
    
    async def register_user(self, username: str, email: str, password: str) -> dict:
        from app.db.database import db_service
        if not db_service.client:
            raise RuntimeError("Database client not initialized")
        try:
            # Check if username or email already exists
            existing = await db_service.client.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?",
                [username, email]
            )
            if existing.rows:
                return {"success": False, "error": "Username or email already exists"}
            # Check if this is the first user
            result = await db_service.client.execute("SELECT COUNT(*) FROM users")
            is_first_user = result.rows[0][0] == 0
            hashed_password = self.get_password_hash(password)
            success = await UserRepository.create(
                username, email, hashed_password, is_admin = is_first_user
            )
            if not success:
                return {"success": False, "error": "Username or email already exists"}
            return {"success": True, "message": "User registered successfully", "is_first_user": is_first_user}
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return {"success": False, "error": "Registration failed"}
    
    async def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate a user and return user data if successful."""
        try:
            # First check if user exists (including inactive)
            user = await UserRepository.get_by_username_including_inactive(username)
            
            if not user:
                return None  # User doesn't exist
            
            # Check if user is inactive
            if not user.get("is_active", True):
                return {"error": "inactive_user"}  # Special error for inactive users
            
            # Check password
            if not self.verify_password(password, user["hashed_password"]):
                return None  # Invalid password
            
            return {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "is_admin": user["is_admin"]
            }
        
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None

    async def authenticate_user_by_email(self, email: str, password: str) -> Optional[dict]:
        """Authenticate a user by email and return user data if successful."""
        try:
            # First check if user exists (including inactive)
            user = await UserRepository.get_by_email_including_inactive(email)
            
            if not user:
                return None  # User doesn't exist
            
            # Check if user is inactive
            if not user.get("is_active", True):
                return {"error": "inactive_user"}  # Special error for inactive users
            
            # Check password
            if not self.verify_password(password, user["hashed_password"]):
                return None  # Invalid password
            
            return {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "is_admin": user["is_admin"]
            }
        
        except Exception as e:
            logger.error(f"Error authenticating user by email: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID."""
        return await UserRepository.get_by_id(user_id)

    async def change_password(self, user_id: str, current_password: str, new_password: str, confirm_password: str) -> dict:
        user = await UserRepository.get_by_id(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        hashed = self.get_password_hash(current_password)
        if not hashed or not hashed.startswith("$2b$"):
            return {"success": False, "error": "Password hash is invalid or missing"}
        if not self.verify_password(current_password, hashed):
            return {"success": False, "error": "Current password is incorrect"}
        if new_password != confirm_password:
            return {"success": False, "error": "New passwords do not match"}
        hashed = self.get_password_hash(new_password)
        from app.db.database import db_service
        if not db_service.client:
            raise RuntimeError("Database client not initialized")
        await db_service.client.execute(
            "UPDATE users SET hashed_password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            [hashed, user_id]
        )
        return {"success": True, "message": "Password updated successfully"}

    async def delete_user_account(self, user_id: str, password: str, require_password: bool = True) -> dict:
        from app.db.database import db_service
        if not db_service.client:
            raise RuntimeError("Database client not initialized")
        try:
            user = await UserRepository.get_by_id(user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Check if password is required and validate it
            if require_password:
                if not password:
                    return {"success": False, "error": "Password is required"}
                hashed = self.get_password_hash(password)
                if not hashed or not self.verify_password(password, hashed):
                    return {"success": False, "error": "Password is incorrect"}
            
            # Delete the user
            result = await db_service.client.execute(
                "DELETE FROM users WHERE id = ?",
                [user_id]
            )
            if result.rows_affected == 0:
                return {"success": False, "error": "User not found or already deleted"}
            return {"success": True, "message": "User account deleted successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def edit_username(self, user_id: str, new_username: str) -> dict:
        from app.db.database import db_service
        if not db_service.client:
            raise RuntimeError("Database client not initialized")
        try:
            # Check if username is taken
            result = await db_service.client.execute(
                "SELECT id FROM users WHERE username = ?",
                [new_username]
            )
            if result.rows:
                return {"success": False, "error": "Username already taken"}
            await db_service.client.execute(
                "UPDATE users SET username = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                [new_username, user_id]
            )
            return {"success": True, "message": "Username updated successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def request_password_reset(self, email: str) -> dict:
        from app.db.database import db_service
        import secrets
        if not db_service.client:
            raise RuntimeError("Database client not initialized")
        try:
            user = await UserRepository.get_by_email(email)
            if not user:
                return {"success": False, "error": "User with this email does not exist"}
            # Generate token
            token = secrets.token_urlsafe(32)
            await db_service.client.execute(
                "CREATE TABLE IF NOT EXISTS password_reset_tokens (email TEXT, token TEXT, expires_at TIMESTAMP)"
            )
            from datetime import datetime, timedelta, timezone
            expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            await db_service.client.execute(
                "INSERT INTO password_reset_tokens (email, token, expires_at) VALUES (?, ?, ?)",
                [email, token, expires_at]
            )
            # Print the reset link (replace with email in production)
            print(f"Password reset link: http://localhost:3000/reset-password?token={token}")
            return {"success": True, "message": "Password reset link sent to email (printed in console for now)."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def hard_reset_password(self, token: str, new_password: str, confirm_password: str) -> dict:
        from app.db.database import db_service
        from datetime import datetime, timezone
        if not db_service.client:
            raise RuntimeError("Database client not initialized")
        try:
            # Find token
            await db_service.client.execute(
                "CREATE TABLE IF NOT EXISTS password_reset_tokens (email TEXT, token TEXT, expires_at TIMESTAMP)"
            )
            result = await db_service.client.execute(
                "SELECT email, expires_at FROM password_reset_tokens WHERE token = ?",
                [token]
            )
            if not result.rows:
                return {"success": False, "error": "Invalid or expired token"}
            email, expires_at = result.rows[0]
            if datetime.now(timezone.utc) > datetime.fromisoformat(expires_at):
                return {"success": False, "error": "Token has expired"}
            if new_password != confirm_password:
                return {"success": False, "error": "New passwords do not match"}
            hashed = self.get_password_hash(new_password)
            await db_service.client.execute(
                "UPDATE users SET hashed_password = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?",
                [hashed, email]
            )
            # Delete the token after use
            await db_service.client.execute(
                "DELETE FROM password_reset_tokens WHERE token = ?",
                [token]
            )
            return {"success": True, "message": "Password reset successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions from the database. Returns number of sessions cleaned."""
        from app.db.database import db_service
        if not db_service.client:
            return 0
        try:
            current_time = datetime.now(timezone.utc)
            cleaned_count = 0
            kept_count = 0
            
            logger.info(f"Starting cleanup at {current_time}")
            
            # Get all sessions and check expiration manually
            result = await db_service.client.execute("SELECT id, session_token, expires_at FROM user_sessions")
            
            logger.info(f"Found {len(result.rows)} total sessions to check")
            
            for row in result.rows:
                session_id, session_token, expires_at_str = row
                try:
                    # Parse the expiration timestamp
                    if isinstance(expires_at_str, str):
                        if 'T' in expires_at_str:
                            # ISO format
                            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                        else:
                            # SQLite format: "2025-07-29 11:53:59"
                            expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                    elif isinstance(expires_at_str, (int, float)):
                        # Handle timestamp as Unix timestamp
                        expires_at = datetime.fromtimestamp(expires_at_str, tz=timezone.utc)
                    elif isinstance(expires_at_str, datetime):
                        # Already a datetime object
                        expires_at = expires_at_str
                    else:
                        logger.error(f"Unknown expires_at type for session {session_id}: {type(expires_at_str)}")
                        continue
                    
                    # Safety check: Only delete if session is actually expired
                    if current_time > expires_at:
                        # Session expired, delete it
                        logger.info(f"Deleting expired session {session_id}, expired at {expires_at}")
                        await db_service.client.execute(
                            "DELETE FROM user_sessions WHERE id = ?",
                            [session_id]
                        )
                        cleaned_count += 1
                    else:
                        # Session is still active, keep it
                        time_remaining = (expires_at - current_time).total_seconds()
                        logger.info(f"Keeping active session {session_id}, expires in {int(time_remaining)} seconds")
                        kept_count += 1
                        
                except Exception as e:
                    logger.error(f"Error parsing session expiration for session {session_id}: {e}")
                    # Don't delete sessions we can't parse - keep them for safety
            
            logger.info(f"Cleanup complete: Deleted {cleaned_count} expired sessions, kept {kept_count} active sessions")
            return cleaned_count
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0

    async def get_active_sessions_count(self) -> int:
        """Get count of active sessions."""
        from app.db.database import db_service
        if not db_service.client:
            logger.warning("Database client not initialized")
            return 0
        try:
            current_time = datetime.now(timezone.utc)
            logger.info(f"Checking active sessions at {current_time}")
            
            # Get all sessions and check expiration manually
            result = await db_service.client.execute("SELECT user_id, expires_at FROM user_sessions")
            
            active_count = 0
            for row in result.rows:
                user_id, expires_at_str = row
                try:
                    # Parse the database timestamp
                    if isinstance(expires_at_str, str):
                        # Handle different timestamp formats
                        if 'T' in expires_at_str:
                            # ISO format
                            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                        else:
                            # SQLite format: "2025-07-29 11:53:59"
                            expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                    elif isinstance(expires_at_str, (int, float)):
                        # Handle timestamp as Unix timestamp
                        expires_at = datetime.fromtimestamp(expires_at_str, tz=timezone.utc)
                    elif isinstance(expires_at_str, datetime):
                        # Already a datetime object
                        expires_at = expires_at_str
                    else:
                        logger.error(f"Unknown expires_at type for user {user_id}: {type(expires_at_str)}")
                        continue
                    
                    if current_time < expires_at:
                        active_count += 1
                        logger.info(f"Active session for user {user_id}, expires at {expires_at}")
                    else:
                        logger.info(f"Expired session for user {user_id}, expired at {expires_at}")
                        
                except Exception as e:
                    logger.error(f"Error parsing session expiration for user {user_id}: {e}")
            
            logger.info(f"Found {active_count} active sessions out of {len(result.rows)} total")
            return active_count
        except Exception as e:
            logger.error(f"Error getting active sessions count: {e}")
            return 0

    async def run_periodic_cleanup(self):
        """Run periodic cleanup of expired sessions and refresh tokens."""
        try:
            logger.info("Running periodic session cleanup...")
            cleaned_count = await self.cleanup_expired_sessions()
            
            # Also cleanup expired refresh tokens
            from app.db.repositories import RefreshTokenRepository
            refresh_cleaned = await RefreshTokenRepository.cleanup_expired()
            
            if cleaned_count > 0 or refresh_cleaned > 0:
                logger.info(f"Periodic cleanup: Removed {cleaned_count} expired sessions, {refresh_cleaned} expired refresh tokens")
            else:
                logger.info("Periodic cleanup: No expired tokens found to remove")
                
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")

    async def get_session_info_for_token(self, token: str) -> Optional[dict]:
        """Get session information for a specific token."""
        from app.db.database import db_service
        if not db_service.client:
            return None
        try:
            result = await db_service.client.execute(
                "SELECT user_id, expires_at FROM user_sessions WHERE session_token = ?",
                [token]
            )
            
            if not result.rows:
                return None
            
            user_id, expires_at_str = result.rows[0]
            current_time = datetime.now(timezone.utc)
            
            # Parse expiration timestamp
            if isinstance(expires_at_str, str):
                if 'T' in expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                else:
                    expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            elif isinstance(expires_at_str, (int, float)):
                # Handle timestamp as Unix timestamp
                expires_at = datetime.fromtimestamp(expires_at_str, tz=timezone.utc)
            elif isinstance(expires_at_str, datetime):
                # Already a datetime object
                expires_at = expires_at_str
            else:
                logger.error(f"Unknown expires_at type: {type(expires_at_str)}")
                return None
            
            time_remaining = (expires_at - current_time).total_seconds()
            
            return {
                "user_id": user_id,
                "expires_at": str(expires_at_str),  # Convert to string for display
                "time_remaining_seconds": max(0, int(time_remaining)),
                "is_expired": time_remaining <= 0
            }
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return None

    async def get_all_sessions_info(self) -> dict:
        """Get information about all sessions for debugging."""
        from app.db.database import db_service
        if not db_service.client:
            return {"error": "Database client not initialized"}
        
        try:
            current_time = datetime.now(timezone.utc)
            result = await db_service.client.execute("SELECT id, user_id, session_token, expires_at FROM user_sessions")
            
            sessions = []
            active_count = 0
            expired_count = 0
            
            for row in result.rows:
                session_id, user_id, session_token, expires_at_str = row
                try:
                    # Parse expiration timestamp - handle all possible data types
                    if isinstance(expires_at_str, str):
                        if 'T' in expires_at_str:
                            # ISO format
                            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                        else:
                            # SQLite format: "2025-07-29 11:53:59"
                            expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                    elif isinstance(expires_at_str, (int, float)):
                        # Handle timestamp as Unix timestamp
                        expires_at = datetime.fromtimestamp(expires_at_str, tz=timezone.utc)
                    elif isinstance(expires_at_str, datetime):
                        # Already a datetime object
                        expires_at = expires_at_str
                    else:
                        # Unknown type, skip this session
                        logger.warning(f"Unknown expires_at type for session {session_id}: {type(expires_at_str)}")
                        sessions.append({
                            "session_id": session_id,
                            "user_id": user_id,
                            "error": f"Unknown expires_at type: {type(expires_at_str)}",
                            "status": "error"
                        })
                        continue
                    
                    time_remaining = (expires_at - current_time).total_seconds()
                    is_expired = time_remaining <= 0
                    
                    if is_expired:
                        expired_count += 1
                    else:
                        active_count += 1
                    
                    sessions.append({
                        "session_id": session_id,
                        "user_id": user_id,
                        "token_preview": session_token[:20] + "..." if len(session_token) > 20 else session_token,
                        "expires_at": str(expires_at_str),  # Convert to string for display
                        "time_remaining_seconds": max(0, int(time_remaining)),
                        "is_expired": is_expired,
                        "status": "expired" if is_expired else "active"
                    })
                    
                except Exception as e:
                    sessions.append({
                        "session_id": session_id,
                        "user_id": user_id,
                        "error": f"Error parsing expiration: {e}",
                        "status": "error"
                    })
            
            return {
                "current_time": current_time.isoformat(),
                "total_sessions": len(sessions),
                "active_sessions": active_count,
                "expired_sessions": expired_count,
                "sessions": sessions
            }
            
        except Exception as e:
            return {"error": f"Error getting sessions info: {e}"}

    async def login_user(self, user_data: dict) -> dict:
        """Login user and return both access and refresh tokens."""
        # Get user role from permissions table (NOT from is_admin field)
        from app.db.repositories import UserPermissionRepository
        user_permission = await UserPermissionRepository.get_by_user_id(str(user_data["id"]))
        
        # IMPORTANT: Role comes from permissions table, not from is_admin field
        # is_admin=true means permanent admin (cannot be changed)
        # is_admin=false means role can be viewer, manager, or temporary admin
        user_role = user_permission.get("role", "viewer") if user_permission else "viewer"
        
        # Include role and permissions in JWT claims for granular access control
        # Note: is_admin is included for reference but NOT used for role verification
        # Get actual permissions from database, grouped by resource type
        from app.db.repositories import RolePermissionRepository
        grouped_permissions = await RolePermissionRepository.get_by_role_grouped(user_role)
        
        # Debug logging to see what's happening
        logger.info(f"User {user_data['id']} - user_permission: {user_permission}")
        logger.info(f"User {user_data['id']} - user_role: {user_role}")
        logger.info(f"User {user_data['id']} - grouped_permissions: {grouped_permissions}")
        
        # Fallback: If no permissions found in database, provide default permissions based on role
        if not grouped_permissions:
            logger.warning(f"No permissions found in database for role '{user_role}', using default permissions")
            if user_role == "admin":
                grouped_permissions = {
                    "workflow": ["read", "write", "execute", "delete", "create", "assign"],
                    "group": ["read", "write", "execute", "delete"]
                }
            elif user_role == "manager":
                grouped_permissions = {
                    "workflow": ["read", "write", "execute", "create"],
                    "group": ["read", "write"]
                }
            elif user_role == "viewer":
                grouped_permissions = {
                    "workflow": ["read", "execute"],
                    "group": ["read"]
                }
            else:
                # Unknown role, default to viewer
                user_role = "viewer"
                grouped_permissions = {
                    "workflow": ["read", "execute"],
                    "group": ["read"]
                }
        
        jwt_data = {
            "sub": str(user_data["id"]),
            "role": user_role,  # This is the actual role from permissions
            "permissions": grouped_permissions,  # Dict of permissions grouped by resource type
            "is_admin": user_data.get("is_admin", False)  # Reference only - not used for role checks
        }
        
        # Create short-lived access token (15 minutes)
        access_token = await self.create_access_token(
            data=jwt_data,
            expires_delta=timedelta(minutes=self.access_token_expire_minutes)
        )
        
        # Create long-lived refresh token (configurable - 5 minutes for testing)
        if self.refresh_token_expire_days < 1:
            # Convert to minutes for short durations
            minutes = int(self.refresh_token_expire_days * 24 * 60)
            refresh_token = await self.create_refresh_token(
                data=jwt_data,
                expires_delta=timedelta(minutes=minutes)
            )
        else:
            refresh_token = await self.create_refresh_token(
                data=jwt_data,
                expires_delta=timedelta(days=self.refresh_token_expire_days)
            )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_data
        }

    async def revoke_all_refresh_tokens(self, user_id: str) -> bool:
        """Revoke all refresh tokens for a user (useful for logout all devices)."""
        from app.db.repositories import RefreshTokenRepository
        return await RefreshTokenRepository.revoke_all_for_user(user_id)

# Global auth service instance
auth_service = AuthService() 