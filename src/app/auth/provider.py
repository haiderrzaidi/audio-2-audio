from abc import ABC, abstractmethod
from enum import Enum

from app.services.auth import TokenData


class AuthProvider(str, Enum):
    STATIC = "STATIC"
    AUTH_SERVICE = "AUTH_SERVICE"


class AuthProviderBase(ABC):
    @abstractmethod
    async def verify(self, token: str) -> TokenData:
        pass


class AuthFactory:
    providers: dict[AuthProvider, AuthProviderBase] = {}
    current_provider: AuthProvider

    def __init__(self, current_provider: str):
        self.current_provider = AuthProvider[current_provider]

    def add_provider(self, name: AuthProvider, provider: AuthProviderBase) -> None:
        if name in self.providers:
            return

        self.providers[name] = provider

    def get_current_provider(self) -> AuthProviderBase:
        if self.current_provider in self.providers:
            return self.providers[self.current_provider]

        raise RuntimeError(f"Current provider {self.current_provider} not registered")
