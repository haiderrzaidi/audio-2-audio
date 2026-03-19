from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @staticmethod
    def connect(uri: str, database_name: str):
        if MongoDB.client is None:
            MongoDB.client = AsyncIOMotorClient(uri)
            MongoDB.db = MongoDB.client[database_name]

    @staticmethod
    def disconnect():
        if MongoDB.client:
            MongoDB.client.close()
            MongoDB.client = None
            MongoDB.db = None
