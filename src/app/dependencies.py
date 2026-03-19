"""All api application dependencies here
"""

from fastapi.templating import Jinja2Templates  # type: ignore
from fastapi.security import OAuth2PasswordBearer  # type: ignore

templates = Jinja2Templates(directory="../views")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user/token")
