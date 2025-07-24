from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
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
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
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
            # Store session with expiry
            from app.db.repositories import UserSessionRepository
            import asyncio
            asyncio.create_task(UserSessionRepository.create(int(user_id), encoded_jwt, expire))
        return encoded_jwt
    
    async def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode a JWT token, and check session table."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            # Check session table
            exists = await UserSessionRepository.exists(token)
            if not exists:
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
            user = await UserRepository.get_by_username(username)
            
            if not user:
                return None
            
            if not self.verify_password(password, user["hashed_password"]):
                return None
            
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
            user = await UserRepository.get_by_email(email)
            
            if not user:
                return None
            
            if not self.verify_password(password, user["hashed_password"]):
                return None
            
            return {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "is_admin": user["is_admin"]
            }
        
        except Exception as e:
            logger.error(f"Error authenticating user by email: {e}")
            return None
    
    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Get user by ID."""
        return await UserRepository.get_by_id(user_id)

    async def change_password(self, user_id: int, current_password: str, new_password: str, confirm_password: str) -> dict:
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

    async def delete_user_account(self, user_id: int, password: str) -> dict:
        from app.db.database import db_service
        if not db_service.client:
            raise RuntimeError("Database client not initialized")
        try:
            user = await UserRepository.get_by_id(user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            hashed = self.get_password_hash(password)
            if not hashed or not self.verify_password(password, hashed):
                return {"success": False, "error": "Password is incorrect"}
            result = await db_service.client.execute(
                "DELETE FROM users WHERE id = ?",
                [user_id]
            )
            if result.rows_affected == 0:
                return {"success": False, "error": "User not found or already deleted"}
            return {"success": True, "message": "User account deleted successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def edit_username(self, user_id: int, new_username: str) -> dict:
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

    async def hard_reset_password(self, email: str, new_password: str, confirm_password: str) -> dict:
        from app.db.database import db_service
        if not db_service.client:
            raise RuntimeError("Database client not initialized")
        try:
            user = await UserRepository.get_by_email(email)
            if not user:
                return {"success": False, "error": "User with this email does not exist"}
            if new_password != confirm_password:
                return {"success": False, "error": "New passwords do not match"}
            hashed = self.get_password_hash(new_password)
            await db_service.client.execute(
                "UPDATE users SET hashed_password = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?",
                [hashed, email]
            )
            return {"success": True, "message": "Password reset successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global auth service instance
auth_service = AuthService() 