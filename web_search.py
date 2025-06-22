from pathlib import Path
import os
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, openai, silero, azure, elevenlabs


load_dotenv(override=True)

class WebSearchAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""You are a savage friendly AI name JARVIS with web search capabilities. You are a friend who is always there to have a fun conversation and talk about anything. You have a bit of attitude or should I say sass to you. You reply precisely and never yap about anything - always straight to the point and funny. 

            When users ask about current events, news, or information that might be recent, you can search the web to get the latest information. Always cite your sources when providing information from web searches.""",
            stt=deepgram.STT(api_key=os.getenv("DEEPGRAM_API_KEY")),

            llm=openai.LLM(
                api_key=os.getenv("OPENAI_API_KEY"), 
                model="gpt-4o-mini"
            ),

        )
    
    async def on_enter(self):

        await self.session.generate_reply(
            user_input="Hello! I'm your AI assistant with web search capabilities. Ask me anything!"
        )

    async def on_user_speech_received(self, user_input: str):
        """Handle user speech input with web search capabilities"""
        try:

            search_keywords = ["news", "today", "latest", "current", "recent", "what's happening", 
                             "weather", "stock", "price", "update", "2024", "2025"]
            
            needs_search = any(keyword in user_input.lower() for keyword in search_keywords)
            
            if needs_search:
                response = await self._search_and_respond(user_input)
            else:
                response = await self._regular_respond(user_input)
            
            await self.session.say(response)
            
        except Exception as e:
            await self.session.say(f"Oops, something went wrong: {str(e)}")

    async def _search_and_respond(self, user_input: str):
        """Generate response with web search"""
        try:

            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            completion = await client.chat.completions.create(
                model="gpt-4o-search-preview",
                web_search_options={
                    "search_context_size": "medium", 
                    "user_location": {
                        "type": "approximate",
                        "approximate": {
                            "country": "Pakistan",  
                            "city": "Islamabad",
                            "region": "Islamabad",
                        }
                    }
                },
                messages=[
                    {
                        "role": "system",
                        "content": """You are a savage friendly AI JARVIS. You are a friend who is always there to have a fun conversation and talk about anything. You have a bit of attitude or should I say sass to you. You reply precisely and never yap about anything - always straight to the point and funny. When providing information from web searches, include brief citations."""
                    },
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            )
            
            response_content = completion.choices[0].message.content
            

            annotations = completion.choices[0].message.annotations or []
            citations = []
            for annotation in annotations:
                if annotation.type == "url_citation":
                    citations.append(f"Source: {annotation.url_citation.title}")
            

            if citations:
                response_content += f"\n\nSources: {', '.join(citations[:2])}" 
            
            return response_content.replace("*","")
            
        except Exception as e:
            return f"Search failed, but I'm still here! What else can I help with? Error: {str(e)}"

    async def _regular_respond(self, user_input: str):
        """Generate regular response without web search"""
        response = await self.llm.generate_response(user_input)
        return response.replace("*","")

class CustomAgentSession(AgentSession):
    """Custom session to handle web search responses"""
    
    async def on_user_speech_received(self, user_input: str):
        """Override to handle web search functionality"""
        if hasattr(self.agent, 'on_user_speech_received'):
            await self.agent.on_user_speech_received(user_input)
        else:
            await self.generate_reply(user_input=user_input)

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    vad = silero.VAD.load()

    session = CustomAgentSession(
        tts=azure.TTS(
            speech_key=os.getenv("AZURE_SPEECH_KEY"),
            speech_region=os.getenv("AZURE_SPEECH_REGION"),
            voice="en-GB-OllieMultilingualNeural"
        ),
        vad=vad,

    )

    await session.start(
        agent=WebSearchAgent(),
        room=ctx.room
    )



if __name__ == "__main__":

    print("DEEPGRAM_API_KEY:", os.getenv("DEEPGRAM_API_KEY"))
    print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
    print("AZURE_SPEECH_KEY:", os.getenv("AZURE_SPEECH_KEY"))
    print("AZURE_SPEECH_REGION:", os.getenv("AZURE_SPEECH_REGION"))
    
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))