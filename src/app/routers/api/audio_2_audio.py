from fastapi import APIRouter, HTTPException  # type: ignore
from fastapi import UploadFile, File  # type: ignore
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse  # type: ignore
from pydantic import BaseModel  # type: ignore
from typing import List
from application_context import chain, streaming_chain, EarVosk, text_to_speech
import torch  # type: ignore
from dotenv import load_dotenv  # type: ignore
import numpy as np  # type: ignore
from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # type: ignore
import uvicorn  # type: ignore
import io
import json
import wave
import logging
import base64
from io import BytesIO

# from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer  # type: ignore
import os

load_dotenv()


# In-memory storage for chat history
chat_history = {}  # type: ignore
# In-memory storage for processed audio paths
audio_paths = {}  # type: ignore
device = "cuda:0" if torch.cuda.is_available() else "cpu"
input_audio = os.getenv("INPUT_AUDIO")
result_audio = os.getenv("RESULT_AUDIO")

# streaming_llm = StreamingLLM(model, tokenizer, device)
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)


class AppState:
    def __init__(self):
        self.llm_chain = None
        self.audio_transcriber = None

    def initialize(self):
        if self.llm_chain is None:
            self.llm_chain = streaming_chain()
        if self.audio_transcriber is None:
            self.audio_transcriber = EarVosk()


app_state = AppState()

router = APIRouter(
    prefix="/tm-audio",
    tags=["Thriving-Minds-Audio"],
)


@router.on_event("startup")
async def startup_event():
    app_state.initialize()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    recognizer = app_state.audio_transcriber.recognizer

    try:
        while True:
            try:
                data = await websocket.receive_bytes()
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())["text"]
                    if result.strip():
                        # Process user input and generate response
                        current_sentence = ""

                        # Generate response and convert to audio chunks
                        for chunk in app_state.llm_chain.stream(
                            {"user_input": result, "chat_history": "[]"}
                        ):
                            print(
                                "🐍 File: api/audio_2_audio.py | Line: 82 | undefined ~ chunk",
                                chunk,
                            )

                            current_sentence += chunk
                            if any(
                                current_sentence.endswith(punct)
                                for punct in [".", "!", "?"]
                            ):
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
                # logger.error(f"Error in websocket handling: {e}")
                break

    except WebSocketDisconnect:
        # logger.info("Client disconnected")
        print("Connection Disconnected")
    except Exception as e:
        print("Connection Closed")
        # logger.error(f"Error in websocket connection: {e}", exc_info=True)
        await websocket.close()
