"""Index page / for the application
this is a non api HTML reponse router
"""

from fastapi import APIRouter  # type: ignore
from fastapi.responses import HTMLResponse  # type: ignore
from fastapi import Request  # type: ignore
from app.dependencies import templates


router = APIRouter(
    prefix="",
    tags=["index"],
    dependencies=[],
    responses={404: {"message": "Not found", "code": 404}},
)


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "data": 10})
