"""Static auth provider. Only used for testing 
Authentication in the app
"""

from app.auth.provider import AuthProviderBase
from app.services import auth as auth_service

from app.services.auth import TokenData


class StaticAuthProvider(AuthProviderBase):
    def __init__(self):
        pass

    async def verify(self, token: str) -> auth_service.TokenData:
        payload = auth_service.verify_token(token)

        return payload
