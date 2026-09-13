from typing import Optional
from pydantic import BaseModel, field_validator


class LoginRequest(BaseModel):
    """Login request body."""
    email: str
    password: str


class RegisterRequest(BaseModel):
    """User registration request body."""
    email: str
    password: str
    password_confirm: str
    role: str  # "officer" or "bidder"
    organization_id: Optional[str] = None  # Required for bidders
    
    @field_validator('email')
    @classmethod
    def valid_email(cls, v: str) -> str:
        """Validate email format."""
        if '@' not in v or '.' not in v.split('@')[1]:
            raise ValueError('Invalid email format')
        return v
    
    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength: at least 8 chars, uppercase, number."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @field_validator('password_confirm')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate passwords match."""
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @field_validator('role')
    @classmethod
    def valid_role(cls, v: str) -> str:
        """Validate role is one of allowed values."""
        if v not in ['officer', 'bidder', 'admin']:
            raise ValueError('Role must be officer, bidder, or admin')
        return v


class TokenResponse(BaseModel):
    """Token response after successful login."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    role: Optional[str] = None  # Added for frontend routing
    user_id: Optional[str] = None  # Added for frontend reference


class UserResponse(BaseModel):
    """User profile response."""
    id: str
    email: str
    role: str
    organization_id: Optional[str] = None
    
    class Config:
        from_attributes = True
