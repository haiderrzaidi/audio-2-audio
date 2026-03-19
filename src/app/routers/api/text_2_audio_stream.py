from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.routers.api.auth_middleware import (
    websocket_auth,
)  # Import the decorator
from fastapi.responses import JSONResponse
import json
from application_context import text_to_speech
from app.services.llm_service import Chatbot_gpt
from dotenv import load_dotenv
import os
import base64
import torch
import logging
from openai import OpenAI
import base64


from app.routers.api import auth_middleware
from fastapi import APIRouter, Depends  # type: ignore
from typing import Union, Annotated

from app.services import auth as auth_service

load_dotenv(override=True)

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


api_key = os.getenv("OPENAI_API_KEY")
# Initialize OpenAI client
client = OpenAI(
    api_key=api_key,
)


def openai_text_to_speech(text):
    """
    Converts text to speech using OpenAI's TTS API.
    Returns base64-encoded audio data in MP3 format.
    """
    try:
        # Call OpenAI TTS API
        response = client.audio.speech.create(
            model="tts-1",  # Use tts-1 for standard quality or tts-1-hd for high quality
            voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
            input=text,
            response_format="mp3",  # Ensure MP3 format for compatibility
        )

        # Read the audio content
        audio_data = response.content

        # Encode audio data to base64
        base64_audio = base64.b64encode(audio_data).decode("utf-8")

        # Return as data URI for direct playback in the browser
        return base64_audio
    except Exception as e:
        print(f"OpenAI TTS Error: {str(e)}")
        return None


import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)


async def openai_text_to_speech_async(text):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, openai_text_to_speech, text)


@router.websocket("/ws_stream_response")
async def websocket_endpoint(
    websocket: WebSocket,
):
    logger.info("PAUSE")

    await websocket.accept()
    chatbot = Chatbot_gpt(logger=logger)
    logger.info("PAUSE")
    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                text_data = message.get("data", "")
                tts_method = message.get("tts", "gtts")  # Default to gTTS
                model_method = message.get("model", "openai")  # Default to openai
                if model_method == "openai":
                    model_type = 1
                else:
                    model_type = 0
                if text_data.strip():
                    current_sentence = ""
                    for chunk in chatbot.run(text_data, model_type):
                        logger.debug(f"Processing chunk: {chunk}")
                        current_sentence += chunk

                        if any(
                            current_sentence.endswith(punct)
                            for punct in [".", "!", "?"]
                        ):
                            # Use selected TTS method
                            if tts_method == "openai":
                                audio_base64 = await openai_text_to_speech_async(
                                    current_sentence.strip()
                                )
                            else:
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
        logger.info("Connection Disconnected")
    except Exception as e:
        logger.error(f"Connection Closed: {e}")
        await websocket.close()
