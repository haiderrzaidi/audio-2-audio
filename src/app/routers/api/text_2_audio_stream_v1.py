from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from application_context import text_to_speech
from app.services.llm_service import Chatbot_gpt
from dotenv import load_dotenv
import os
import base64
import torch
import logging
from app.services.db.chat_history_service import ChatHistoryService

load_dotenv()

# Initialize the logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# In-memory storage for chat history
device = "cuda:0" if torch.cuda.is_available() else "cpu"


# App state initialization
class AppState:
    def __init__(self):
        self.llm_chain = None

    def initialize(self):
        if self.llm_chain is None:
            self.chatbot = Chatbot_gpt(logger=logger)


app_state = AppState()

router = APIRouter(
    prefix="/tm-text-audio",
    tags=["Thriving-Minds-Audio"],
)


@router.on_event("startup")
async def startup_event():
    app_state.initialize()


@router.websocket("/ws_stream_response_v1")
async def websocket_endpoint(websocket: WebSocket, user_id: str = Query(...)):
    await websocket.accept()
    chatbot = Chatbot_gpt(logger=logger)

    # Create a chat session for the user and send the session ID to the frontend
    session = await ChatHistoryService.create_session(user_id=user_id)
    session_id = session.id  # MongoDB _id
    await websocket.send_json({"type": "session_id", "session_id": session_id})

    try:
        while True:
            try:
                # Receive text input and session ID from the WebSocket
                message_data = await websocket.receive_json()
                session_id = message_data.get("session_id")
                text_data = message_data.get("text")

                if not session_id or not text_data:
                    raise ValueError("Session ID and text must be provided.")

                # Add the user's message to the chat history
                await ChatHistoryService.add_message(
                    session_id=session_id, role="user", content=text_data
                )

                if text_data.strip():
                    current_sentence = ""
                    response_text = ""

                    # Generate response and process in chunks
                    for chunk in chatbot.run(text_data):
                        logger.debug(f"Processing chunk: {chunk}")

                        current_sentence += chunk
                        response_text += chunk

                        if any(
                            current_sentence.endswith(punct)
                            for punct in [".", "!", "?"]
                        ):
                            # Convert completed sentence to speech
                            audio_base64 = text_to_speech(current_sentence.strip())
                            if audio_base64:
                                response = {
                                    "type": "audio",
                                    "text": current_sentence.strip(),
                                    "audio": audio_base64,
                                    "has_more": True,
                                }
                                await websocket.send_json(response)
                            current_sentence = ""

                    # Add assistant's response to the chat history
                    await ChatHistoryService.add_message(
                        session_id=session_id, role="assistant", content=response_text
                    )

                    # Send end-of-stream signal
                    await websocket.send_json(
                        {
                            "type": "audio",
                            "text": "Stream-End",
                            "audio": None,
                            "has_more": False,
                        }
                    )
            except Exception as e:
                logger.error(f"Error in WebSocket handling: {e}")
                break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
    except Exception as e:
        logger.error(f"WebSocket connection closed with error: {e}")
        await websocket.close()
