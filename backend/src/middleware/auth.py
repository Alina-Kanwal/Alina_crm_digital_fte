"""
Authentication and authorization middleware for the Digital FTE agent.
Handles JWT token validation and role-based access control.
"""
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from typing import Optional

# Security
security = HTTPBearer()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def create_access_token(data: dict, expires_delta: Optional[int] = None):
    """
    Create a JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = expires_delta
    else:
        expire = JWT_EXPIRATION_HOURS * 3600
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = security):
    """
    Dependency to get current user from JWT token.
    """
    token = credentials.credentials
    payload = verify_token(token)
    # In a real app, you'd fetch user from database here
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return {"id": user_id, **payload}

# Role-based access control decorators
def require_role(allowed_roles: list):
    """
    Decorator to require specific roles for endpoint access.
    Usage: @require_role(["admin", "agent"])
    """
    def role_checker(current_user: dict = get_current_user):
        user_role = current_user.get("role", "user")
        if user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker