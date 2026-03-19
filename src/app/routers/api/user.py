"""User api router module
All user related endpoints including the 
auth endpoints for users are included
"""
# src/app/routers/api/user.py
from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore
from fastapi.security import OAuth2PasswordRequestForm  # type: ignore

from typing import Annotated
from utils import get_logger

import app.services.user as user_service
import app.services.auth as auth_service
from app.routers.api import auth_middleware

from datetime import timedelta

import os

ACCESS_TOKEN_EXPIRE_HOURS = int(os.environ["AUTH_ACCESS_TOKEN_EXPIRE_HOURS"])

logger = get_logger("user_router")

router = APIRouter(
    prefix="/user",
    tags=["user"],
    dependencies=[],
    responses={},
)


# @router.post("/token2")
# async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
#     user_: dict | None = None
#     try:
#         user_ = await user_service.get_user(form_data.username)
#     except Exception as ex:
#         raise HTTPException(
#             status_code=401,
#             detail=(
#                 f"User matching username '{form_data.username}' "
#                 f"or password `{form_data.password}` not found"
#             ),
#         ) from ex

#     if not user_:
#         raise HTTPException(status_code=400, detail="Incorrect username or password")

#     user = user_service.UserSchema(**user_)

#     hashed_password = auth_service.hash_password(form_data.password)
#     if not hashed_password == user.hashed_password:
#         raise HTTPException(status_code=400, detail="Incorrect username or password")

#     return {"access_token": user.username, "token_type": "bearer"}


@router.get("/users/me")
async def read_users_me(
    current_user: Annotated[
        user_service.UserSchema, Depends(auth_middleware.extract_user_middleware)
    ]
):
    return current_user


@router.post("/token", response_model=auth_service.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = auth_service.create_access_token(
        data={"sub": user.username, "user_id": str(user.id)},  # Add user_id here
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}
