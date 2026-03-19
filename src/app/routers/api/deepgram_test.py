from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Deepgram API Key
API_KEY = os.getenv("DEEPGRAM_API_KEY")

router = APIRouter(prefix="/stt-tm-text-audios", tags=["Thriving-Minds-Audio"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established")

    # Create an event loop reference
    loop = asyncio.get_event_loop()

    # Queue for transcription results and events
    transcript_queue = asyncio.Queue()

    try:
        # Initialize Deepgram client
        deepgram = DeepgramClient(api_key=API_KEY)
        dg_connection = deepgram.listen.live.v("1")

        # Define event handlers
        def on_open(self, open, **kwargs):
            print("Deepgram connection opened")
            loop.call_soon_threadsafe(transcript_queue.put_nowait, "Connection opened")

        def on_message(self, result, **kwargs):
            try:
                if result.speech_final:  # Only send finalized transcripts
                    sentence = result.channel.alternatives[0].transcript
                    if len(sentence) > 0:
                        print(f"Transcription (speech_final): {sentence}")
                        loop.call_soon_threadsafe(transcript_queue.put_nowait, sentence)
            except Exception as e:
                print(f"Error in on_message: {e}")
                loop.call_soon_threadsafe(
                    transcript_queue.put_nowait, f"Error in transcription: {e}"
                )

        def on_speech_started(self, speech_started, **kwargs):
            print("Speech started")
            loop.call_soon_threadsafe(transcript_queue.put_nowait, "[Speech Started]")

        def on_utterance_end(self, utterance_end, **kwargs):
            print("Utterance ended")
            loop.call_soon_threadsafe(transcript_queue.put_nowait, "[Utterance Ended]")

        def on_error(self, error, **kwargs):
            print(f"Error: {error}")
            loop.call_soon_threadsafe(transcript_queue.put_nowait, f"Error: {error}")

        def on_close(self, close, **kwargs):
            print("Deepgram connection closed")
            loop.call_soon_threadsafe(transcript_queue.put_nowait, "Connection closed")

        # Register event handlers
        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
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
            utterance_end_ms="2000",
            vad_events=True,
            endpointing=300,
        )

        # Start Deepgram connection
        if not dg_connection.start(options):
            raise Exception("Failed to start Deepgram connection")
        print("Deepgram connection started")

        # Async task to process audio
        async def process_audio():
            while True:
                try:
                    audio_data = await asyncio.wait_for(
                        websocket.receive_bytes(), timeout=30.0
                    )
                    dg_connection.send(audio_data)
                except asyncio.TimeoutError:
                    print("No audio data received for 30 seconds")
                    break
                except WebSocketDisconnect:
                    print("WebSocket disconnected")
                    break

        # Async task to send transcriptions and events
        async def send_transcriptions():
            while True:
                try:
                    transcript = await transcript_queue.get()
                    await websocket.send_text(transcript)
                    transcript_queue.task_done()
                except Exception as e:
                    print(f"Error sending transcription: {e}")
                    break

        # Create and run tasks
        audio_task = asyncio.create_task(process_audio())
        transcript_task = asyncio.create_task(send_transcriptions())

        # Wait for tasks to complete
        await asyncio.gather(audio_task, transcript_task, return_exceptions=True)

    except Exception as e:
        print(f"An error occurred: {e}")
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        try:
            dg_connection.finish()
        except:
            pass
        await websocket.close()
        print("WebSocket connection closed")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
