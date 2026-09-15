"""JWT authentication and password hashing for Phase 0."""
import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# Security setup - use argon2 for better reliability
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production-12345")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))


def hash_password(password: str) -> str:
    """Hash password using bcrypt.
    
    Args:
        password: Plain-text password to hash
        
    Returns:
        Hashed password (bcrypt)
    """
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against bcrypt hash.
    
    Args:
        password: Plain-text password to verify
        password_hash: Hashed password from database
        
    Returns:
        True if password matches hash, False otherwise
    """
    return pwd_context.verify(password, password_hash)


def create_access_token(user_id: str, role: str, expires_in_minutes: Optional[int] = None) -> str:
    """Create JWT access token.
    
    Args:
        user_id: UUID of the user
        role: User role (bidder, officer, admin)
        expires_in_minutes: Token expiration in minutes (uses JWT_EXPIRATION_MINUTES if not specified)
        
    Returns:
        JWT token string
    """
    if expires_in_minutes is None:
        expires_in_minutes = JWT_EXPIRATION_MINUTES
    
    expire = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    to_encode = {
        "sub": str(user_id),  # subject (user_id)
        "role": role,
        "exp": expire,
    }
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode and validate JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary with user_id and role
        
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None or role is None:
            raise JWTError("Invalid token payload: missing user_id or role")
        return {"user_id": user_id, "role": role}
    except JWTError as e:
        raise JWTError(f"Could not validate credentials: {str(e)}")
