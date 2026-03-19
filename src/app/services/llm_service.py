import os
from openai import OpenAI
from dotenv import load_dotenv
import logging


class BaseChatbot:
    def __init__(self, logger=None):
        self.logger = logger


class Chatbot_gpt(BaseChatbot):
    def __init__(
        self,
        sys_prompt="",
        Model="qwen2.5-coder:32b",
        api_key="",
        api_key2="",
        base_url="",
        max_tokens=None,
        logger=None,
    ):
        super().__init__(logger=logger)
        load_dotenv()

        if api_key == "":
            api_key = os.getenv("OPEN_SOURCE_API")
        if api_key2 == "":
            api_key2 = os.getenv("OPENAI_API_KEY")

        if base_url == "":
            base_url = os.getenv("BASE_URL")
        if sys_prompt == "":
            prompt_file_path = os.path.join(
                os.path.dirname(__file__),
                "../../../data/prompt/chat_system_prompt_v2.txt",
            )
            with open(prompt_file_path, "r") as file:
                sys_prompt = file.read()
        if max_tokens is None:
            max_tokens = int(os.getenv("MAX_TOKEN", 1000))

        self.MODEL = Model
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.client2 = OpenAI(api_key=api_key2)

        self.messages = [{"role": "system", "content": sys_prompt}]
        self.max_tokens = max_tokens

    def run(self, input_text, client):
        self.messages.append({"role": "user", "content": input_text})
        finished = False
        response = ""

        while not finished:
            if client == 0:
                stream = self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=self.messages,
                    stream=True,
                    max_tokens=self.max_tokens,
                )
            else:
                stream = self.client2.chat.completions.create(
                    model="gpt-4o-mini-2024-07-18",
                    messages=self.messages,
                    stream=True,
                    max_tokens=self.max_tokens,
                )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    response += chunk.choices[0].delta.content
                    if self.logger != None:
                        self.logger.debug(
                            f"Processing chunk: {chunk.choices[0].delta.content}"
                        )
                    print(chunk.choices[0].delta.content, end="")
                    yield chunk.choices[0].delta.content
                finish_reason = chunk.choices[0].finish_reason
                if finish_reason == "stop":
                    finished = True

        self.messages.append({"role": "assistant", "content": response})

    def generate_title(self) -> str:
        title = ""
        messages = [
            {
                "role": "system",
                "content": f"""Given entire chat history generate a small chat title of at max 5 words.
                        Chat History:
                        {self.messages}
                     """,
            }
        ]
        stream = self.client.chat.completions.create(
            model=self.MODEL,
            messages=messages,
            max_tokens=self.max_tokens,
        )
        return stream.choices[0].message.content


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Create an instance of the Chatbot_gpt
    chatbot = Chatbot_gpt(logger=logger)  # type: ignore
    counter = 0
    # Test the chatbot with a sample input
    while True:
        input_text = input("Enter your message: ")
        print("Chatbot response:")
        for i in chatbot.run(input_text, 0):
            pass
        print("\n")
        if counter == 2:
            print("\nChatbot title:", chatbot.generate_title())
        counter += 1
