from typing import Optional

from groq import Groq

from intelligence.intelligence import Intelligence
from tts.tts import TTS


class GroqIntelligence(Intelligence):
    def __init__(self, api_key: str, tts: TTS, model: Optional[str] = None, system_prompt: Optional[str] = None):
        self.client = Groq(
            api_key=api_key,
        )

        self.tts = tts
        self.system_prompt = "You are AI Interviewer and you are interviewing a candidate for a software engineering position."
        self.chat_history = []
        self.model = model or "llama3-8b-8192"
        self.system_prompt = system_prompt or "You are AI Interviewer and you are interviewing a candidate for a software engineering position."

        self.pubsub = None
    
    def set_pubsub(self, pubsub):
        self.pubsub = pubsub
    def build_messages(
        self,
        text: str,
        sender_name: str,
    ):
        # TODO: generate context related to text
        context = ""

        # Build the message
        human_message = {
            "role": "user",
            "type": "human",
            "name": sender_name.replace(" ", "_"),
            "content": text,
        }

        # Add message to history
        self.chat_history.append(human_message)

        # Local chat history limited to few messages
        chat_history = []

        # Add system message and generated context
        chat_history.append(
            {
                "role": "system",
                "type": "system",
                "content": self.system_prompt,
            }
        )

        # Add few messages from global history
        chat_history = chat_history + self.chat_history[-20:]

        # Return local chat history
        return chat_history
    
    def add_response(self, text):
        ai_message = {
            "role": "assistant",
            "type": "ai",
            "name": "Interviewer",
            "content": text,
        }

        self.chat_history.append(ai_message)

    def text_generator(self, response):
       for chunk in response:
          content = chunk.choices[0].delta.content
          if content:
            yield content

    def generate(self, text: str, sender_name: str):
        # build old history
        messages = self.build_messages(text, sender_name=sender_name)

        # generate llm completion
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=100,
            temperature=0.5,
            stream=False
        )
        response_text = ""

        # TODO: handle stream response and generate text chunk by chunk
        # text_iterator = self.text_generator(response)
        # self.tts.generate(text=text_iterator)

        # generate text as a block
        response_text = response.choices[0].message.content
        self.tts.generate(text=response_text)

        print(f"[Interviewer]: {response_text}")
        if self.pubsub is not None:
            # publish in meeting
            self.pubsub(message=f"[Interviewer]: {response_text}")

        # add response to history
        self.add_response(response_text)
