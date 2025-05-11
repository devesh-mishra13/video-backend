# auth_utils.py
from passlib.context import CryptContext
import jwt
import os
from datetime import datetime, timedelta

# Set up the password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Secret key for signing the JWT token (keep it secure in production)
SECRET_KEY = os.getenv("JWT_SECRET")

# Hash a password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Verify a password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Create JWT token with expiration
def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=7)):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + expires_delta})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
