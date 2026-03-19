""" Index API router. at the momenet used as a sample
"""

from fastapi import APIRouter, Depends  # type: ignore
from typing import Union, Annotated

from app.services import auth as auth_service
from app.services import user as user_service

from app.routers.api import auth_middleware

from utils import get_logger


logger = get_logger("api index")

router = APIRouter(
    prefix="/item",
    tags=["item"],
    dependencies=[],
    responses={404: {"message": "Not found", "code": 404}},
)


@router.get("/items/{item_id}")
def read_item(
    item_id: int,
    current_user: Annotated[
        user_service.UserSchema, Depends(auth_middleware.extract_user_middleware)
    ],
    q: Union[str, None] = None,
):
    logger.info(f"Got user {current_user}")
    return {"item_id": item_id, "q": q}


@router.put("/items")
def read_item_put(item_id: int):
    return {"item_id": item_id}


@router.get("/test")
def test_endpoint(
    payload: Annotated[
        auth_service.TokenData, Depends(auth_middleware.verify_token_middleware)
    ]
):
    logger.info(f"Got payload {payload}")
    return {"message": "successful test"}
