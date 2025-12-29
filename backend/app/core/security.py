"""Security utilities for authentication and password handling."""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import secrets
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.core.token_blacklist import token_blacklist

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    if "jti" not in to_encode:
        to_encode["jti"] = secrets.token_urlsafe(16)

    to_encode.update({"exp": expire, "type": "access", "iat": int(datetime.utcnow().timestamp())})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with separate secret for rotation."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    if "jti" not in to_encode:
        to_encode["jti"] = secrets.token_urlsafe(16)
    to_encode.update({"exp": expire, "type": "refresh", "iat": int(datetime.utcnow().timestamp())})
    encoded_jwt = jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Decode and verify a JWT token.
    
    Args:
        token: JWT token to decode
        token_type: "access" or "refresh" - determines which secret to use
    """
    try:
        secret_key = settings.REFRESH_SECRET_KEY if token_type == "refresh" else settings.SECRET_KEY
        payload = jwt.decode(token, secret_key, algorithms=[settings.ALGORITHM])
        
        # Verify token type matches
        if payload.get("type") != token_type:
            return None
        
        return payload
    except JWTError:
        return None


async def validate_access_token(token: str) -> Optional[dict]:
    """Decode access token and verify it is not blacklisted."""
    payload = decode_token(token, token_type="access")
    if not payload:
        return None
    jti = payload.get("jti")
    if jti and await token_blacklist.is_blacklisted(jti):
        return None
    return payload


def create_token_pair(data: dict) -> Tuple[str, str]:
    """Create both access and refresh tokens.
    
    Returns:
        Tuple of (access_token, refresh_token)
    """
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    return access_token, refresh_token
