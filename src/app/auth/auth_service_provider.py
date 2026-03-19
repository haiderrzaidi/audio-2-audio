from app.auth.provider import AuthProviderBase
from app.services.auth import TokenData
import httpx
import os

from utils import get_logger


logger = get_logger("auth_middleware")


class AuthServiceProvider(AuthProviderBase):
    def __init__(self):
        self.auth_service_uri = os.getenv("AUTH_SERVICE_URI")

    async def verify(self, token: str) -> TokenData:
        async with httpx.AsyncClient() as client:
            try:
                # Use the environment-configured URL
                url = f"{self.auth_service_uri}/api/v1/user/profile/self"
                logger.debug(f"Auth service verification URL: {url}")

                response = await client.get(
                    url, headers={"Authorization": f"Bearer {token}"}, timeout=10
                )

                logger.debug(f"Auth response status: {response.status_code}")
                logger.debug(f"Auth response body: {response.text}")

                response.raise_for_status()
                user_data = response.json()

                return TokenData(
                    user_id=str(user_data.get("id")),
                    username=user_data.get("email"),  # email -> username
                    email=user_data.get("email"),
                )

            except httpx.HTTPStatusError as exc:
                error_msg = f"Auth service error: {exc.response.status_code} {exc.response.text}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            except Exception as exc:
                logger.error(f"Auth verification failed: {str(exc)}", exc_info=True)
                raise
