from datetime import datetime

from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from .mongodb_service import MongoDB


class PydanticObjectId(ObjectId):
    """Custom Pydantic type for MongoDB ObjectId."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = datetime.utcnow()


class ChatSession(BaseModel):
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    user_id: str
    title: str
    messages: List[ChatMessage] = []
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Config:
        allow_population_by_field_name = True  # Allow `_id` to map to `id`
        json_encoders = {ObjectId: str}  # Convert ObjectId to string in JSON


class ChatHistoryService:
    collection_name = "chat_sessions"

    @staticmethod
    def get_collection():
        if MongoDB.db is None:
            raise ValueError("Database connection is not initialized.")
        return MongoDB.db[ChatHistoryService.collection_name]

    @staticmethod
    async def create_session(user_id: str) -> ChatSession:
        """Create a new chat session and return the session with its MongoDB `_id`."""
        collection = ChatHistoryService.get_collection()

        session = ChatSession(user_id=user_id, messages=[])
        result = await collection.insert_one(
            session.dict(by_alias=True, exclude={"id"})
        )
        session.id = result.inserted_id  # Set the MongoDB `_id` to the session
        return session

    @staticmethod
    async def get_session(session_id: str) -> Optional[ChatSession]:
        """Retrieve a session by its MongoDB `_id`."""
        collection = ChatHistoryService.get_collection()
        session_data = await collection.find_one({"_id": ObjectId(session_id)})
        if session_data:
            return ChatSession(**session_data)
        return None

    @staticmethod
    async def add_message(session_id: str, role: str, content: str):
        """Add a message to an existing session."""
        collection = ChatHistoryService.get_collection()
        message = ChatMessage(role=role, content=content)
        await collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$push": {"messages": message.dict()},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )

    @staticmethod
    async def add_title(session_id: str, title: str):
        """Add a title to session."""
        collection = ChatHistoryService.get_collection()
        await collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$push": {"title": title},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )

    @staticmethod
    async def get_chat_history(session_id: str) -> List[ChatMessage]:
        """Get the message history for a session."""
        session = await ChatHistoryService.get_session(session_id)
        if session:
            return session.messages
        return []

    @staticmethod
    async def delete_session(session_id: str):
        """Delete a session by its MongoDB `_id`."""
        collection = ChatHistoryService.get_collection()
        await collection.delete_one({"_id": ObjectId(session_id)})
