"""
API Key + JWT Authentication Module

Supports two auth methods:
  1. Simple API Key: X-API-Key header
  2. JWT Token: Authorization: Bearer <token> header
"""
import os
import jwt
import time
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer(auto_error=False)


def verify_api_key(request: Request) -> str:
    """Verify API Key from X-API-Key header."""
    api_key = request.headers.get("X-API-Key")
    expected_key = os.getenv("AGENT_API_KEY", "sk-test-key")
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if api_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user_id from key (e.g., sk-user-123 → user-123)
    user_id = api_key.split("-", 1)[1] if "-" in api_key else "anonymous"
    return user_id


def create_token(username: str, role: str = "user") -> str:
    """Create JWT token."""
    payload = {
        "sub": username,
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """Verify JWT token from Authorization header."""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role", "user")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return {"user_id": user_id, "role": role}
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
