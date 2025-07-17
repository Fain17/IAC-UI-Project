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
        """Register a new user."""
        try:
            # Hash password and create user
            hashed_password = self.get_password_hash(password)
            success = await UserRepository.create(username, email, hashed_password)
            
            if not success:
                return {"success": False, "error": "Username or email already exists"}
            
            return {"success": True, "message": "User registered successfully"}
        
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
                "email": user["email"]
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
                "email": user["email"]
            }
        
        except Exception as e:
            logger.error(f"Error authenticating user by email: {e}")
            return None
    
    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Get user by ID."""
        return await UserRepository.get_by_id(user_id)

# Global auth service instance
auth_service = AuthService() 