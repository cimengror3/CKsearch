"""
CKSEARCH API - Authentication Helper
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings

# Password hashing (untuk future use)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer()


def create_admin_token(data: dict) -> str:
    """Create JWT token untuk admin."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours)
    to_encode.update({"exp": expire, "type": "admin"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token dari admin."""
    token = credentials.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "admin":
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


def verify_admin_secret(secret: str) -> bool:
    """Verify admin secret."""
    return secret == settings.admin_secret


def generate_license_key() -> str:
    """Generate random license key format: XXXX-XXXX-XXXX-XXXX"""
    import secrets
    import string
    chars = string.ascii_uppercase + string.digits
    parts = [''.join(secrets.choice(chars) for _ in range(4)) for _ in range(4)]
    return '-'.join(parts)


def generate_referral_code() -> str:
    """Generate random referral code (8 chars)."""
    import secrets
    import string
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))
