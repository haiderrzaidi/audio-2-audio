from pathlib import Path
import os
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, openai, silero, azure

# Load .env variables
load_dotenv(override=True)

class UninterruptableAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a savage friendly AI. You are a friend who is always there to have a fun conversation and talk about anything. You have a bit attitude or shoud i say sass to you. You reply precisely. You never yap about anything always straight to the point and funny.",
            stt=deepgram.STT(api_key=os.getenv("DEEPGRAM_API_KEY")),
            llm=openai.LLM(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o"),
            tts=openai.TTS(api_key=os.getenv("OPENAI_API_KEY")),
            # We leave vad unset here—session will provide it
        )

    async def on_enter(self):
        self.session.generate_reply(
            user_input="You are a savage friendly AI. You are a friend who is always there to have a fun conversation and talk about anything. You have a bit attitude or shoud i say sass to you. You reply precisely. You never yap about anything always straight to the point and funny."
        )

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    # Load the Silero VAD, ideally before handling jobs
    vad = silero.VAD.load()

    session = AgentSession(
    # tts=azure.TTS(
    #     speech_key=os.getenv("AZURE_SPEECH_KEY"),
    #     speech_region=os.getenv("AZURE_SPEECH_REGION"),
    #     voice="en-GB-OllieMultilingualNeural"
    # ),
        vad=vad,
        # Note: no turn_detection specified => defaults to VAD only
    )

    await session.start(
        agent=UninterruptableAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    # Debug prints to verify env variables
    print("DEEPGRAM_API_KEY:", os.getenv("DEEPGRAM_API_KEY"))
    print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
