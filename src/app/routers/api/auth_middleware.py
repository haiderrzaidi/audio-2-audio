"""Auth middlewares to be used as a dependency to 
fastapi routes or routers

"""

from app.services import auth as auth_service
from app.services import user as user_service
from app.auth.auth_factory import auth_factory
from app.dependencies import oauth2_scheme
from fastapi import HTTPException, status, Depends, Header, WebSocketException

# type: ignore
from typing import Annotated
from jose import jwt  # type: ignore
from passlib.context import CryptContext  # type: ignore
from fastapi import WebSocket, status  # type: ignore
from fastapi.exceptions import HTTPException
from typing import Callable, Awaitable, Any
from functools import wraps

from app.services.auth import TokenData

from utils import get_logger


logger = get_logger("auth_middleware")


async def websocket_auth(websocket: WebSocket) -> TokenData:
    await websocket.accept()
    authorization = websocket.headers.get("Authorization")
    if not authorization:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Missing token"
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication scheme",
        )

    auth_provider = auth_factory.get_current_provider()
    try:
        token_data = await auth_provider.verify(token)
        return token_data
    except Exception as e:
        logger.error(f"WebSocket auth failed: {str(e)}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
        )


async def verify_token_middleware(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> auth_service.TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not verify credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # payload = auth_service.verify_token(token)
        payload = await auth_factory.get_current_provider().verify(token)
        return payload
    except Exception as ex:
        msg = str(ex)
        credentials_exception.detail = credentials_exception.detail + f":  {msg}"
        raise credentials_exception from ex


async def decode_token_middleware(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> auth_service.TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate and decode credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # payload = await auth_service.decode_token(token)
        payload = await auth_factory.get_current_provider().verify(token)
        return payload
    except Exception as ex:
        raise credentials_exception from ex


async def extract_user_middleware(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> user_service.UserSchema:
    """
    Gets the current user by decoding the token received from the header
    as a bearer token
    """
    try:
        # token_data = await auth_service.decode_token(token)
        payload = await auth_factory.get_current_provider().verify(token)
        if payload.username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="username on token not found",
            )

        user = await user_service.get_user(payload.username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not fetch user with username `{payload.username}`",
            )
        return user

    except HTTPException as ex:
        raise ex

    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unable to extract user: `{str(ex)}`",
        ) from ex


def websocket_auth_required(func):
    @wraps(func)
    async def wrapper(websocket: WebSocket, *args, **kwargs):
        logger.info(f"New WS connection attempt from {websocket.client}")
        auth_header = websocket.headers.get("Authorization")

        if not auth_header:
            logger.error("No Authorization header in WS connection")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        try:
            token = auth_header.split(" ")[1].strip()
            logger.debug(f"Token received: {token[:6]}...{token[-6:]}")

            provider = auth_factory.get_current_provider()
            logger.info(f"Using auth provider: {provider.__class__.__name__}")

            token_data = await provider.verify(token)
            logger.info(f"Authentication successful for: {token_data}")

            # Validate required fields
            if not token_data.user_id or not token_data.username:
                logger.error("Token missing required fields")
                raise ValueError("Invalid token data")

        except Exception as e:
            logger.error(f"WS auth failed: {str(e)}", exc_info=True)
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()
        logger.info("WebSocket connection established successfully")
        return await func(websocket, token_data, *args, **kwargs)

    return wrapper
