from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import json
from application_context import streaming_chain, text_to_speech
from dotenv import load_dotenv
import os
import base64
import torch

load_dotenv()

# In-memory storage for chat history
device = "cuda:0" if torch.cuda.is_available() else "cpu"


# App state initialization
class AppState:
    def __init__(self):
        self.llm_chain = None

    def initialize(self):
        if self.llm_chain is None:
            self.llm_chain = streaming_chain()


app_state = AppState()

router = APIRouter(
    prefix="/tm-text-audio",
    tags=["Thriving-Minds-Audio"],
)


@router.on_event("startup")
async def startup_event():
    app_state.initialize()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            try:
                # Receive text input from the WebSocket
                text_data = await websocket.receive_text()

                if text_data.strip():
                    current_sentence = ""

                    # Generate response and convert to audio chunks
                    for chunk in app_state.llm_chain.stream(
                        {"user_input": text_data, "chat_history": "[]"}
                    ):
                        print(
                            "🐍 Processing chunk:",
                            chunk,
                        )

                        current_sentence += chunk
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
                                }
                                await websocket.send_json(response)
                            current_sentence = ""

                    # Handle any remaining text
                    if current_sentence.strip():
                        audio_base64 = text_to_speech(current_sentence.strip())
                        if audio_base64:
                            response = {
                                "type": "audio",
                                "text": current_sentence.strip(),
                                "audio": audio_base64,
                            }
                            await websocket.send_json(response)

            except Exception as e:
                print(f"Error in WebSocket handling: {e}")
                break

    except WebSocketDisconnect:
        print("Connection Disconnected")
    except Exception as e:
        print(f"Connection Closed: {e}")
        await websocket.close()
