"""Authentication logic goes here
"""

from app.services import user as user_service
from pydantic import BaseModel  # type: ignore
from datetime import datetime, timedelta

from jose import jwt  # type: ignore
from passlib.context import CryptContext  # type: ignore
import os


SECRET_KEY = os.environ["AUTH_SECRET_KEY"]
ALGORITHM = os.environ["AUTH_ALGORITHM"]
ACCESS_TOKEN_EXPIRE_HOURS = os.environ["AUTH_ACCESS_TOKEN_EXPIRE_HOURS"]


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: str | None = None
    email: str | None = None
    username: str | None = None


def verify_token(token: str) -> TokenData:
    options = {
        "verify_signature": False,
        "verify_exp": True,
        "require_sub": True,
        "verify_sub": True,
        "require_exp": True,
    }

    payload = jwt.decode(token, "", algorithms=None, options=options)
    username: str | None = payload.get("sub")
    if username is None:
        raise RuntimeError("username (sub) not present in token")
    token_data = TokenData(username=username)
    return token_data


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def decode_token(token: str) -> TokenData:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str | None = payload.get("sub")
    if username is None:
        raise RuntimeError("Username (sub) not found on the token payload")
    token_data = TokenData(username=username)
    return token_data


async def authenticate_user(username: str, password: str) -> user_service.UserSchema:
    user = await user_service.get_user(username)
    if not user:
        raise RuntimeError(f"User with username `{username}` not found")

    if not verify_password(password, user.hashed_password):
        raise RuntimeError("Unable to verify password with stored hash")
    return user
