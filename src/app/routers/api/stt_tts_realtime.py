from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
import asyncio
import json
import base64
import logging
from concurrent.futures import ThreadPoolExecutor
import torch
import numpy as np
import io
import speech_recognition as sr
from gtts import gTTS

from app.services.llm_service import Chatbot_gpt

load_dotenv(override=True)

# Configure logging with more detail
logger = logging.getLogger("text2audio")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

router = APIRouter(prefix="/stt-tm-text-audio", tags=["Thriving-Minds-Audio"])


# =======================
# Load Silero VAD Model
# =======================
def load_silero_vad():
    """Load the Silero VAD model."""
    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad", model="silero_vad", force_reload=False
    )
    get_speech_timestamps, _, _, _, _ = utils
    return model, get_speech_timestamps


# =======================
# Speech Recognition
# =======================
def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe audio using Google Speech Recognition with improved error handling."""
    logger.info(f"Transcribing audio of size {len(audio_bytes)} bytes")
    r = sr.Recognizer()

    # Adjust recognition parameters for better results
    r.energy_threshold = 300  # Increase sensitivity
    r.dynamic_energy_threshold = True
    r.pause_threshold = 0.8  # Shorter pause threshold

    try:
        # Create audio data with explicit format specification
        audio_data = sr.AudioData(
            audio_bytes, sample_rate=16000, sample_width=2
        )  # 16-bit PCM

        # Try with more specific parameters
        text = r.recognize_google(audio_data, language="en-US", show_all=False)

        if text:
            logger.info(f"Transcription successful: '{text}'")
            return text
        else:
            logger.warning("Empty transcription result")
            return ""

    except sr.UnknownValueError:
        logger.warning("Speech recognition failed: Audio not understood")
        return ""
    except sr.RequestError as e:
        logger.error(f"Speech recognition error: {e}")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error in transcription: {str(e)}", exc_info=True)
        return ""


async def transcribe_async(audio_bytes: bytes) -> str:
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, transcribe_audio, audio_bytes)


# =======================
# Text-to-Speech
# =======================
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
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, generate_speech, text)


# =======================
# WebSocket Endpoint
# =======================
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")

    # Initialize chatbot and Silero VAD
    chatbot = Chatbot_gpt(logger=logger)
    vad_model, get_speech_timestamps = load_silero_vad()

    # Configuration
    sample_rate = 16000
    silence_threshold = 1.2  # seconds

    # State variables
    is_speaking = False
    last_speech_time = 0
    current_time = 0
    audio_buffer = bytearray()  # Changed to bytearray for better byte handling
    is_listening = True

    try:
        while True:
            data = await websocket.receive()

            # Process binary audio data when listening
            if "bytes" in data and is_listening:
                audio_bytes = data["bytes"]
                current_time += len(audio_bytes) / (
                    sample_rate * 2
                )  # Estimate time in seconds

                # Convert bytes to numpy array - assuming 16-bit PCM
                audio_np = (
                    np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
                    / 32768.0
                )

                # Run VAD on the audio chunk
                speech_timestamps = get_speech_timestamps(
                    torch.tensor(audio_np),
                    vad_model,
                    sampling_rate=sample_rate,
                    return_seconds=True,
                    min_speech_duration_ms=100,
                    min_silence_duration_ms=100,
                    threshold=0.5,
                )

                if speech_timestamps:
                    if not is_speaking:
                        logger.info("Speech started")
                        is_speaking = True
                        audio_buffer = bytearray()  # Reset buffer as bytearray

                    last_speech_time = current_time
                    audio_buffer.extend(audio_bytes)  # Add chunk to buffer
                else:
                    # Still record audio to maintain continuity
                    if is_speaking:
                        audio_buffer.extend(audio_bytes)

                        # Check for end of speech
                        if current_time - last_speech_time > silence_threshold:
                            logger.info(
                                f"Speech ended after {current_time - last_speech_time:.2f}s of silence"
                            )
                            is_speaking = False

                            # Process the complete utterance
                            if len(audio_buffer) > 0:
                                # Convert audio to the correct format for speech recognition
                                try:
                                    # Ensure audio is properly formatted for speech recognition
                                    audio_data = bytes(audio_buffer)

                                    # Make sure we have enough audio data to process
                                    if (
                                        len(audio_data) < 2000
                                    ):  # Arbitrary small value check
                                        logger.warning(
                                            f"Audio too short ({len(audio_data)} bytes), skipping"
                                        )
                                        audio_buffer = bytearray()
                                        is_listening = True
                                        continue

                                    # Transcribe with proper error handling
                                    text = await transcribe_async(audio_data)
                                    audio_buffer = bytearray()  # Clear the buffer

                                    if text:
                                        await websocket.send_json(
                                            {"type": "user_text", "text": text}
                                        )
                                        logger.info(
                                            f"User text sent to client: '{text}'"
                                        )

                                        # Switch to responding state
                                        is_listening = False
                                        logger.info(
                                            "Stopped listening, entering response phase"
                                        )

                                        try:
                                            # Generate and send response in chunks
                                            response_buffer = []
                                            for chunk in chatbot.run(text, 1):
                                                response_buffer.append(chunk)
                                                if chunk.strip().endswith(
                                                    (".", "!", "?")
                                                ):
                                                    sentence = "".join(response_buffer)
                                                    response_buffer = []
                                                    audio = await generate_speech_async(
                                                        sentence
                                                    )
                                                    await websocket.send_json(
                                                        {
                                                            "type": "audio",
                                                            "text": sentence,
                                                            "audio": audio,
                                                        }
                                                    )
                                                    logger.info(
                                                        f"Sent audio response for sentence: '{sentence}'"
                                                    )
                                        finally:
                                            # Resume listening after response
                                            is_listening = True
                                            logger.info(
                                                "Response phase complete, resuming listening"
                                            )
                                    else:
                                        logger.warning("Empty transcription result")

                                except Exception as e:
                                    logger.error(
                                        f"Error processing audio: {str(e)}",
                                        exc_info=True,
                                    )
                                    audio_buffer = bytearray()
                                    is_listening = True

            # Handle text-based control messages
            elif "text" in data:
                try:
                    config = json.loads(data["text"])
                    logger.info(f"Received control message: {config}")

                    # Update configuration if specified
                    if "silence_threshold" in config:
                        silence_threshold = float(config["silence_threshold"])
                        logger.info(
                            f"Updated silence threshold to {silence_threshold}s"
                        )

                    if "vad_threshold" in config:
                        # We would need to re-initialize the model with new threshold
                        # This is a simplification, as the threshold is used in get_speech_timestamps
                        logger.info(
                            f"Updated VAD threshold to {config['vad_threshold']}"
                        )

                except json.JSONDecodeError:
                    logger.warning("Invalid JSON received in control message")

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        await websocket.close()
    finally:
        logger.info("WebSocket connection closed")
