"""The main fastapi app module

Returns:
    None
"""

import os
from fastapi import FastAPI, APIRouter  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.staticfiles import StaticFiles  # type: ignore

from utils import get_logger
from app.routers import index
from app.routers import thriving_minds_demo

from app.routers.api import user
from app.routers.api import index as api_index
# from app.routers.api import text_2_audio as TM_text_audio
from app.routers.api import text_2_audio_stream as TM_text_audio_stream
# from app.routers.api import stt_tts_realtime as TM_text_audio_stream_v4
# from app.routers.api import deepgram_test as TM_text_audio_stream_v5

# from app.routers.api import audio_2_audio as TM_audio
from app.routers.api import thriving_minds_chat as TM_chat

from .services.db.mongodb_service import MongoDB

# from dotenv import load_dotenv
# load_dotenv(get_full_path("../.env"))

logger = get_logger("main")

description = """
Centrox AI template. Fire way!! 🚀

## APIs and usecases implemented on this server:
- usecase 1
- usecase 2

"""

app = FastAPI(
    title="Centrox AI Template",
    description=description,
    summary="This App is for Thriving Minds Your Personal Assistant",
    version="0.0.1",  # run to get current version: semantic-release version --print
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Haider Zaidi",
        "url": "https://www.centrox.ai",
        "email": "zaidihaider336@gmail.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redocs",
)


def apply_origins(application: FastAPI):
    origins: str | None = os.getenv("ORIGINS")
    if origins is None:
        origins = "*"

    origins_lst = origins.split(",")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins_lst,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return origins


origins_applied = apply_origins(app)
app.mount("/public", StaticFiles(directory="../public"), name="public")


# @app.on_event("startup")
# async def startup_event():
#     mongo_uri = os.getenv("MONGODB_URI")
#     if not mongo_uri:
#         raise ValueError("MONGODB_URI environment variable not set")
#     MongoDB.connect(uri=mongo_uri, database_name="TM_Chatbot")


# @app.on_event("shutdown")
# async def shutdown_event():
#     MongoDB.disconnect()


logger.info(f"Accepting from origins {origins_applied}")
app.include_router(index.router)
app.include_router(thriving_minds_demo.chat_router)  # Chatbot frontend
app.include_router(thriving_minds_demo.audio_router)  # Audio frontend
app.include_router(thriving_minds_demo.text_audio_router)  # Text Audio frontend
app.include_router(thriving_minds_demo.realtime_router)  # Text Audio frontend


api_v1_router = APIRouter(
    prefix="/api/v1",
    tags=[],
    dependencies=[],
    responses={404: {"message": "Not found", "code": 404}},
)

"""
Include All of the application api routers to this 
router object
"""
api_v1_router.include_router(api_index.router)

api_v1_router.include_router(user.router)

api_v1_router.include_router(TM_chat.router)

# app.include_router(TM_audio.router)

# app.include_router(TM_text_audio.router)

app.include_router(TM_text_audio_stream.router)

# app.include_router(TM_text_audio_stream_v4.router)
# app.include_router(TM_text_audio_stream_v5.router)

app.include_router(api_v1_router)
