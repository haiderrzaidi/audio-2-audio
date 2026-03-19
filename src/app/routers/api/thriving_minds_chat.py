from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import os
from dotenv import load_dotenv
import asyncio
import json
import base64
import logging
from concurrent.futures import ThreadPoolExecutor
from gtts import gTTS
import io

from app.services.llm_service import Chatbot_gpt

# Load environment variables
load_dotenv(override=True)

# Configure logging
logger = logging.getLogger("text2audio")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

router = APIRouter(prefix="/stt-tm-text-audio", tags=["Thriving-Minds-Audio"])

# Deepgram API Key
API_KEY = os.getenv("DEEPGRAM_API_KEY")


# Text-to-Speech Functions
def generate_speech(text: str) -> str:
    """Convert text to speech using gTTS."""
    logger.info(f"Generating speech for text: '{text}'")
    tts = gTTS(text=text, lang="en")
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    audio_data = mp3_fp.read()
    encoded_audio = base64.b64encode(audio_data).decode("utf-8")
    logger.info(f"Speech generated, size: {len(audio_data)} bytes")
    return encoded_audio


async def generate_speech_async(text: str) -> str:
    """Asynchronous wrapper for generate_speech."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, generate_speech, text)


# WebSocket Endpoint
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")

    # Initialize chatbot and Deepgram client
    chatbot = Chatbot_gpt(logger=logger)
    deepgram = DeepgramClient(api_key=API_KEY)
    dg_connection = deepgram.listen.live.v("1")

    # State variables
    accumulated_text = ""  # To accumulate transcription until utterance ends
    utterances_queue = asyncio.Queue()  # Queue for processing utterances
    is_listening = True  # Control whether to process new transcriptions

    # Get the current event loop
    loop = asyncio.get_event_loop()

    # Define Deepgram event handlers
    def on_open(self, open, **kwargs):
        logger.info("Deepgram connection opened")

    def on_message(self, result, **kwargs):
        nonlocal accumulated_text, is_listening
        if result.speech_final and is_listening:
            sentence = result.channel.alternatives[0].transcript
            if sentence:
                accumulated_text += " " + sentence
                logger.info(f"Transcription segment: '{sentence}'")

    def on_utterance_end(self, utterance_end, **kwargs):
        nonlocal accumulated_text, is_listening
        if accumulated_text and is_listening:
            # Safely queue the utterance using the main event loop
            asyncio.run_coroutine_threadsafe(
                utterances_queue.put(accumulated_text.strip()), loop
            )
            accumulated_text = ""
            logger.info("Utterance ended, queued for processing")

    def on_error(self, error, **kwargs):
        logger.error(f"Error: {error}")

    def on_close(self, close, **kwargs):
        logger.info("Deepgram connection closed")

    # Register event handlers
    dg_connection.on(LiveTranscriptionEvents.Open, on_open)
    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)
    dg_connection.on(LiveTranscriptionEvents.Close, on_close)

    # Configure Deepgram options
    options = LiveOptions(
        model="nova-2",
        language="en-US",
        smart_format=True,
        encoding="linear16",
        channels=1,
        sample_rate=16000,
        punctuate=True,
        interim_results=True,
        utterance_end_ms="2000",  # 2 seconds of silence to end utterance
        vad_events=True,
        endpointing=300,  # Finalize transcript after 300ms of silence
    )

    # Start Deepgram connection
    if not dg_connection.start(options):
        raise Exception("Failed to start Deepgram connection")
    logger.info("Deepgram connection started")

    # Task to process utterances
    async def process_utterances():
        nonlocal is_listening
        while True:
            text = await utterances_queue.get()
            if text and is_listening:
                # Send user transcription to client
                await websocket.send_json({"type": "user_text", "text": text})
                logger.info(f"User text sent to client: '{text}'")

                # Switch to responding state
                is_listening = False
                logger.info("Stopped listening, entering response phase")

                try:
                    # Generate and send response in chunks
                    response_buffer = []
                    for chunk in chatbot.run(text, 1):
                        response_buffer.append(chunk)
                        if chunk.strip().endswith((".", "!", "?")):
                            sentence = "".join(response_buffer)
                            response_buffer = []
                            audio = await generate_speech_async(sentence)
                            await websocket.send_json(
                                {"type": "audio", "text": sentence, "audio": audio}
                            )
                            logger.info(
                                f"Sent audio response for sentence: '{sentence}'"
                            )
                finally:
                    # Resume listening after response
                    is_listening = True
                    logger.info("Response phase complete, resuming listening")
            utterances_queue.task_done()

    # Task to process incoming audio
    async def process_audio():
        while True:
            try:
                audio_data = await asyncio.wait_for(
                    websocket.receive_bytes(), timeout=30.0
                )
                dg_connection.send(audio_data)
            except asyncio.TimeoutError:
                logger.info("No audio data received for 30 seconds")
                break
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                break

    # Create and run tasks
    process_utterances_task = asyncio.create_task(process_utterances())
    process_audio_task = asyncio.create_task(process_audio())

    try:
        await asyncio.gather(process_utterances_task, process_audio_task)
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        dg_connection.finish()
        await websocket.close()
        logger.info("WebSocket connection closed")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
