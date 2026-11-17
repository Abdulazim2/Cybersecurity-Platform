
from dotenv import load_dotenv

load_dotenv()

import os
import jwt

from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash


# Password hashing configuration
password_hash = PasswordHash.recommended()


# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is missing from environment variables")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Hash a password
def hash_password(password: str) -> str:
    return password_hash.hash(password)


# Verify a password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


# Create JWT access token
def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    token = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


# Verify JWT access token
def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload

    except jwt.InvalidTokenError:
        return None

# ==========================================
# Factory Sensor Security
# ==========================================

import secrets
import hashlib
import hmac


# Generate a secure random token for a factory sensor
def generate_sensor_token() -> str:
    return secrets.token_urlsafe(32)


# Hash a sensor token using SHA-256
def hash_sensor_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# Verify a sensor token against its stored hash
def verify_sensor_token(token: str, stored_hash: str) -> bool:
    if not token or not stored_hash:
        return False

    token_hash = hash_sensor_token(token)

    return hmac.compare_digest(token_hash, stored_hash)
