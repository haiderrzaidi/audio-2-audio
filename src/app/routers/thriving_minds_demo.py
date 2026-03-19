from fastapi import APIRouter  # type: ignore
from fastapi.responses import FileResponse  # type: ignore
import os
from dotenv import load_dotenv

load_dotenv(override=True)


def sanitize_path(path):
    # Strip unwanted characters and resolve to absolute path
    return os.path.abspath(path.strip()) if path else None


# Paths for frontend files
chat_frontend_path = str(os.getenv("CHAT_HTML"))
audio_frontend_path = str(os.getenv("AUDIO_HTML"))
text_audio_frontend_path = str(os.getenv("TEXT_AUDIO_HTML"))
realtime_frontend_path = sanitize_path(os.getenv("REALTIME_HTML", ""))

# Router for chatbot demo
chat_router = APIRouter(
    prefix="/chat-demo",
    tags=["chatbot_demo"],
    responses={404: {"message": "Not found", "code": 404}},
)


@chat_router.get("/", response_class=FileResponse)
async def read_chat():
    return FileResponse(chat_frontend_path)


# Router for audio demo
audio_router = APIRouter(
    prefix="/audio-demo",
    tags=["audio_demo"],
    responses={404: {"message": "Not found", "code": 404}},
)


@audio_router.get("/", response_class=FileResponse)
async def read_audio():
    return FileResponse(audio_frontend_path)


# Router for audio demo
text_audio_router = APIRouter(
    prefix="/text-audio-demo",
    tags=["text_audio_demo"],
    responses={404: {"message": "Not found", "code": 404}},
)


@text_audio_router.get("/", response_class=FileResponse)
async def read_text_audio():
    return FileResponse(text_audio_frontend_path)


realtime_router = APIRouter(
    prefix="/realtime-demo",
    tags=["realtime_demo"],
    responses={404: {"message": "Not found", "code": 404}},
)


@realtime_router.get("/", response_class=FileResponse)
async def ws_reminder_flow():
    return FileResponse(realtime_frontend_path)
