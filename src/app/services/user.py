"""User service with methods related to user business logic
"""

from typing import Dict
from pydantic import BaseModel  # type: ignore


class User(BaseModel):
    id: str  # Add this line
    username: str
    email: str


class UserSchema(User):
    hashed_password: str


users_db: Dict[str, UserSchema] = {
    "ai": UserSchema(
        **{
            "username": "ai",
            "id": "1",  # Add this
            "email": "template@centrox.ai",
            "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password: secret
        },
    ),
}


async def get_user(username: str) -> UserSchema | None:
    """
    This should call some sort of db or service to get
    user information
    """
    return users_db.get(username, None)
