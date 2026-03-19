from fastapi import APIRouter, HTTPException  # type: ignore
from fastapi.responses import JSONResponse  # type: ignore
from pydantic import BaseModel  # type: ignore
from typing import List
from application_context import chain
import torch  # type: ignore
from dotenv import load_dotenv  # type: ignore
import numpy as np  # type: ignore
import os

load_dotenv()

router = APIRouter(
    prefix="/tm-chat",
    tags=["Thriving-Minds-Audio"],
)


class ChatMessage(BaseModel):
    role: str
    message: str


class ChatHistory(BaseModel):
    session_id: str
    chat_history: List[ChatMessage]


streaming_llm = chain()


@router.post("/tm/summaries")
async def chat_summary(chat_request: ChatHistory):
    try:
        # Prepare chat history for the model
        chat_history = "\n".join(
            [f"{msg.role}: {msg.message}" for msg in chat_request.chat_history]
        )
        user_input = "Summarize the above chat history."

        # Generate summary
        summary = streaming_llm.predict(
            chat_history=chat_history, user_input=user_input
        )

        return JSONResponse(content={"summary": summary}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
