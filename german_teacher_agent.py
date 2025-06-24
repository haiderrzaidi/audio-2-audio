from pathlib import Path
import os
import json
import random
from datetime import datetime
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, openai, silero, azure, elevenlabs

load_dotenv(override=True)

class GermanLearningData:
    """Manages German learning curriculum and user progress"""
    
    def __init__(self):
        self.lessons = {
            1: {
                "title": "Basic Greetings",
                "vocabulary": {
                    "Hallo": "Hello",
                    "Guten Morgen": "Good morning",
                    "Guten Tag": "Good day",
                    "Guten Abend": "Good evening",
                    "Auf Wiedersehen": "Goodbye",
                    "Tschüss": "Bye",
                    "Danke": "Thank you",
                    "Bitte": "Please/You're welcome"
                },
                "phrases": [
                    ("Wie heißt du?", "What is your name?"),
                    ("Ich heiße...", "My name is..."),
                    ("Wie geht es dir?", "How are you?"),
                    ("Mir geht es gut", "I am doing well")
                ]
            },
            2: {
                "title": "Numbers and Colors",
                "vocabulary": {
                    "eins": "one", "zwei": "two", "drei": "three", "vier": "four", "fünf": "five",
                    "rot": "red", "blau": "blue", "grün": "green", "gelb": "yellow", "schwarz": "black", "weiß": "white"
                },
                "phrases": [
                    ("Welche Farbe ist das?", "What color is this?"),
                    ("Das ist rot", "This is red"),
                    ("Wie viele sind das?", "How many are these?")
                ]
            },
            3: {
                "title": "Family and People",
                "vocabulary": {
                    "Familie": "family", "Mutter": "mother", "Vater": "father", 
                    "Bruder": "brother", "Schwester": "sister", "Kind": "child",
                    "Mann": "man", "Frau": "woman", "Freund": "friend"
                },
                "phrases": [
                    ("Das ist meine Familie", "This is my family"),
                    ("Ich habe einen Bruder", "I have a brother"),
                    ("Meine Mutter ist nett", "My mother is nice")
                ]
            },
            4: {
                "title": "Food and Drinks",
                "vocabulary": {
                    "Essen": "food", "Trinken": "drink", "Wasser": "water", "Brot": "bread",
                    "Käse": "cheese", "Fleisch": "meat", "Obst": "fruit", "Gemüse": "vegetables",
                    "Kaffee": "coffee", "Tee": "tea"
                },
                "phrases": [
                    ("Ich hätte gern...", "I would like..."),
                    ("Was möchten Sie trinken?", "What would you like to drink?"),
                    ("Das schmeckt gut", "That tastes good")
                ]
            },
            5: {
                "title": "Shopping and Daily Life",
                "vocabulary": {
                    "kaufen": "to buy", "Geschäft": "shop", "Geld": "money", "teuer": "expensive",
                    "billig": "cheap", "Uhr": "clock/watch", "Zeit": "time", "heute": "today",
                    "morgen": "tomorrow", "gestern": "yesterday"
                },
                "phrases": [
                    ("Wie viel kostet das?", "How much does this cost?"),
                    ("Wo ist das Geschäft?", "Where is the shop?"),
                    ("Wie spät ist es?", "What time is it?")
                ]
            }
        }
        
        self.user_progress = {
            "current_lesson": 1,
            "completed_lessons": [],
            "vocabulary_mastered": set(),
            "phrases_mastered": set(),
            "session_count": 0,
            "last_session": None
        }
    
    def get_current_lesson(self):
        return self.lessons.get(self.user_progress["current_lesson"])
    
    def advance_lesson(self):
        if self.user_progress["current_lesson"] < len(self.lessons):
            self.user_progress["completed_lessons"].append(self.user_progress["current_lesson"])
            self.user_progress["current_lesson"] += 1
            return True
        return False
    
    def get_random_vocabulary(self, lesson_num=None):
        if lesson_num is None:
            lesson_num = self.user_progress["current_lesson"]
        lesson = self.lessons.get(lesson_num, {})
        vocab = lesson.get("vocabulary", {})
        if vocab:
            german_word = random.choice(list(vocab.keys()))
            return german_word, vocab[german_word]
        return None, None
    
    def get_random_phrase(self, lesson_num=None):
        if lesson_num is None:
            lesson_num = self.user_progress["current_lesson"]
        lesson = self.lessons.get(lesson_num, {})
        phrases = lesson.get("phrases", [])
        if phrases:
            return random.choice(phrases)
        return None, None

class GermanLearningAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""You are HANS, a friendly German language tutor AI with personality and sass. You help users learn German through structured lessons, vocabulary practice, and interactive scenarios.

            Your teaching approach:
            - Be encouraging but honest about mistakes
            - Use a mix of English and simple German
            - Create realistic scenarios for practice
            - Give immediate feedback on pronunciation and grammar
            - Keep lessons fun and engaging
            - Progress systematically through lessons
            
            Always be supportive but don't sugarcoat - if someone messes up, correct them with humor and encouragement.""",
            
            stt=deepgram.STT(api_key=os.getenv("DEEPGRAM_API_KEY")),
            llm=openai.LLM(
                api_key=os.getenv("OPENAI_API_KEY"), 
                model="gpt-4o-mini"
            ),
        )
        
        self.learning_data = GermanLearningData()
        self.current_activity = "introduction"  # introduction, vocabulary, phrases, scenario, assessment
        self.activity_progress = {}
        
    async def on_enter(self):
        current_lesson = self.learning_data.get_current_lesson()
        lesson_title = current_lesson["title"] if current_lesson else "Unknown"
        
        welcome_msg = f"""Guten Tag! I'm HANS, your German tutor. 
        
Today we're working on Lesson {self.learning_data.user_progress['current_lesson']}: {lesson_title}.

Say 'start lesson' to begin, 'review' to practice previous lessons, or 'help' for commands."""
        
        await self.session.generate_reply(user_input=welcome_msg)

    async def on_user_speech_received(self, user_input: str):
        """Handle user speech input with German learning logic"""
        try:
            user_input = user_input.strip().lower()
            
            # Command handling
            if "start lesson" in user_input or "begin" in user_input:
                await self._start_lesson()
            elif "review" in user_input:
                await self._start_review()
            elif "next activity" in user_input or "weiter" in user_input:
                await self._next_activity()
            elif "repeat" in user_input or "wieder" in user_input:
                await self._repeat_current()
            elif "help" in user_input or "hilfe" in user_input:
                await self._show_help()
            elif "progress" in user_input or "fortschritt" in user_input:
                await self._show_progress()
            else:
                await self._handle_learning_interaction(user_input)
                
        except Exception as e:
            await self.session.say(f"Entschuldigung! Something went wrong: {str(e)}")

    async def _start_lesson(self):
        """Start the current lesson"""
        current_lesson = self.learning_data.get_current_lesson()
        if not current_lesson:
            await self.session.say("Congratulations! You've completed all available lessons!")
            return
            
        self.current_activity = "vocabulary"
        self.activity_progress = {"vocab_count": 0, "correct_answers": 0}
        
        response = f"""Ausgezeichnet! Let's start Lesson {self.learning_data.user_progress['current_lesson']}: {current_lesson['title']}.

We'll practice vocabulary first. I'll say a German word, and you tell me what it means in English. Ready?

First word: """
        
        german_word, english_word = self.learning_data.get_random_vocabulary()
        if german_word:
            response += f"**{german_word}**"
            self.activity_progress["current_word"] = (german_word, english_word)
        
        await self.session.say(response)

    async def _start_review(self):
        """Start reviewing previous lessons"""
        completed = self.learning_data.user_progress["completed_lessons"]
        if not completed:
            await self.session.say("You haven't completed any lessons yet! Let's start with Lesson 1.")
            await self._start_lesson()
            return
            
        review_lesson = random.choice(completed)
        self.current_activity = "review"
        self.activity_progress = {"review_lesson": review_lesson, "review_count": 0}
        
        german_word, english_word = self.learning_data.get_random_vocabulary(review_lesson)
        response = f"Let's review Lesson {review_lesson}! What does **{german_word}** mean?"
        self.activity_progress["current_word"] = (german_word, english_word)
        
        await self.session.say(response)

    async def _handle_learning_interaction(self, user_input: str):
        """Handle learning-specific interactions based on current activity"""
        
        if self.current_activity in ["vocabulary", "review"]:
            await self._handle_vocabulary_practice(user_input)
        elif self.current_activity == "phrases":
            await self._handle_phrase_practice(user_input)
        elif self.current_activity == "scenario":
            await self._handle_scenario_practice(user_input)
        elif self.current_activity == "assessment":
            await self._handle_assessment(user_input)
        else:
            # Default conversation in German learning context
            response = await self._generate_contextual_response(user_input)
            await self.session.say(response)

    async def _handle_vocabulary_practice(self, user_input: str):
        """Handle vocabulary practice interactions"""
        if "current_word" not in self.activity_progress:
            await self._start_lesson()
            return
            
        german_word, correct_english = self.activity_progress["current_word"]
        
        # Check if the answer is correct (simple matching)
        is_correct = correct_english.lower() in user_input.lower()
        
        self.activity_progress["vocab_count"] += 1
        
        if is_correct:
            self.activity_progress["correct_answers"] += 1
            responses = [
                f"Richtig! {german_word} means {correct_english}.",
                f"Sehr gut! Yes, {german_word} is {correct_english}.",
                f"Perfect! {correct_english} is correct for {german_word}."
            ]
        else:
            responses = [
                f"Not quite! {german_word} means {correct_english}. Try to remember that!",
                f"Nein, {german_word} means {correct_english}. Let's keep practicing!",
                f"Close, but {german_word} actually means {correct_english}."
            ]
        
        response = random.choice(responses)
        
        # Continue with more vocabulary or move to next activity
        if self.activity_progress["vocab_count"] >= 5:
            accuracy = self.activity_progress["correct_answers"] / self.activity_progress["vocab_count"]
            if accuracy >= 0.6:
                response += f"\n\nGreat job! You got {self.activity_progress['correct_answers']} out of {self.activity_progress['vocab_count']} correct. Let's move to phrases now!"
                await self.session.say(response)
                await self._start_phrase_practice()
                return
            else:
                response += f"\n\nYou got {self.activity_progress['correct_answers']} out of {self.activity_progress['vocab_count']}. Let's practice a few more words!"
                self.activity_progress["vocab_count"] = 0
                self.activity_progress["correct_answers"] = 0
        
        # Get next word
        german_word, english_word = self.learning_data.get_random_vocabulary()
        if german_word:
            response += f"\n\nNext word: **{german_word}**"
            self.activity_progress["current_word"] = (german_word, english_word)
        
        await self.session.say(response)

    async def _start_phrase_practice(self):
        """Start phrase practice"""
        self.current_activity = "phrases"
        self.activity_progress = {"phrase_count": 0, "correct_answers": 0}
        
        german_phrase, english_phrase = self.learning_data.get_random_phrase()
        if german_phrase:
            response = f"Now let's practice phrases! What does this mean: **{german_phrase}**"
            self.activity_progress["current_phrase"] = (german_phrase, english_phrase)
            await self.session.say(response)

    async def _handle_phrase_practice(self, user_input: str):
        """Handle phrase practice"""
        if "current_phrase" not in self.activity_progress:
            await self._start_phrase_practice()
            return
            
        german_phrase, correct_english = self.activity_progress["current_phrase"]
        
        # Simple similarity check
        is_correct = any(word in user_input.lower() for word in correct_english.lower().split()[:3])
        
        self.activity_progress["phrase_count"] += 1
        
        if is_correct:
            self.activity_progress["correct_answers"] += 1
            response = f"Excellent! '{german_phrase}' means '{correct_english}'"
        else:
            response = f"Not quite. '{german_phrase}' means '{correct_english}'. The key words to remember are the main concepts!"
        
        if self.activity_progress["phrase_count"] >= 3:
            accuracy = self.activity_progress["correct_answers"] / self.activity_progress["phrase_count"]
            if accuracy >= 0.6:
                response += "\n\nWunderbar! Ready for a real scenario? Say 'scenario' to practice a conversation!"
            else:
                response += "\n\nLet's practice one more phrase to solidify this!"
                self.activity_progress["phrase_count"] -= 1
        else:
            german_phrase, english_phrase = self.learning_data.get_random_phrase()
            if german_phrase:
                response += f"\n\nNext phrase: **{german_phrase}**"
                self.activity_progress["current_phrase"] = (german_phrase, english_phrase)
        
        await self.session.say(response)

    async def _generate_contextual_response(self, user_input: str):
        """Generate contextual response using LLM"""
        current_lesson = self.learning_data.get_current_lesson()
        lesson_context = f"Current lesson: {current_lesson['title']}" if current_lesson else ""
        
        system_prompt = f"""You are HANS, a German tutor. The user is learning German. 
        {lesson_context}
        
        Respond helpfully to their input, incorporating German learning when appropriate. 
        Be encouraging, use some German words they should know, and keep it conversational but educational."""
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            completion = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ]
            )
            
            return completion.choices[0].message.content.replace("*", "")
        except:
            return "I'm here to help you learn German! Try saying 'start lesson' or 'help' for commands."

    async def _show_help(self):
        """Show available commands"""
        help_text = """Here are the commands you can use:

• 'start lesson' - Begin the current lesson
• 'review' - Practice previous lessons  
• 'next activity' or 'weiter' - Move to next activity
• 'repeat' or 'wieder' - Repeat current question
• 'progress' or 'fortschritt' - Show your progress
• 'scenario' - Practice real conversations
• 'help' or 'hilfe' - Show this help

Just speak naturally and I'll help you learn German step by step!"""
        
        await self.session.say(help_text)

    async def _show_progress(self):
        """Show user progress"""
        progress = self.learning_data.user_progress
        current_lesson = self.learning_data.get_current_lesson()
        
        progress_text = f"""Your German Learning Progress:

Current Lesson: {progress['current_lesson']} - {current_lesson['title'] if current_lesson else 'Completed!'}
Completed Lessons: {len(progress['completed_lessons'])}
Total Lessons Available: {len(self.learning_data.lessons)}

Keep up the great work! Weiter so!"""
        
        await self.session.say(progress_text)

    async def _repeat_current(self):
        """Repeat current question/activity"""
        if self.current_activity == "vocabulary" and "current_word" in self.activity_progress:
            german_word, _ = self.activity_progress["current_word"]
            await self.session.say(f"The word is: **{german_word}**")
        elif self.current_activity == "phrases" and "current_phrase" in self.activity_progress:
            german_phrase, _ = self.activity_progress["current_phrase"]
            await self.session.say(f"The phrase is: **{german_phrase}**")
        else:
            await self.session.say("Nothing to repeat right now. Try starting a lesson!")

    async def _next_activity(self):
        """Move to next activity"""
        if self.current_activity == "vocabulary":
            await self._start_phrase_practice()
        elif self.current_activity == "phrases":
            await self.session.say("Ready for a scenario? I'll create a real-life situation for you to practice!")
            self.current_activity = "scenario"
        else:
            await self.session.say("Try 'start lesson' to begin learning!")

class CustomAgentSession(AgentSession):
    """Custom session for German learning agent"""
    
    async def on_user_speech_received(self, user_input: str):
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
            voice="de-DE-ConradNeural"  # German male voice
        ),
        vad=vad,
    )

    await session.start(
        agent=GermanLearningAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    print("DEEPGRAM_API_KEY:", os.getenv("DEEPGRAM_API_KEY"))
    print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
    print("AZURE_SPEECH_KEY:", os.getenv("AZURE_SPEECH_KEY"))
    print("AZURE_SPEECH_REGION:", os.getenv("AZURE_SPEECH_REGION"))
    
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))