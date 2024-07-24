import os
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from openai import OpenAI
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()


class LLMClient(ABC):
    @abstractmethod
    def send_message(
        self,
        system_prompt: str,
        user_prompt: str,
        message_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        pass


class OllamaClient(LLMClient):
    def __init__(self):
        self.client = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1")

    def send_message(
        self,
        system_prompt: str,
        user_prompt: str,
        message_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        if message_history:
            messages = message_history + messages

        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"An error occurred with Ollama: {str(e)}"


class OpenAIClient(LLMClient):
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "NONE"))
        self.model = os.getenv("OPENAI_MODEL", "NONE")

    def send_message(
        self,
        system_prompt: str,
        user_prompt: str,
        message_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        if message_history:
            messages = message_history + messages

        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"An error occurred with OpenAI: {str(e)}"


class LLMManager:
    def __init__(self, default_client: str = "ollama"):
        self.clients = {"ollama": OllamaClient(), "openai": OpenAIClient()}
        self.default_client = default_client

    def send_message(
        self,
        system_prompt: str,
        user_prompt: str,
        client: Optional[str] = None,
        message_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        client = client or self.default_client
        if client not in self.clients:
            raise ValueError(f"Invalid client: {client}")

        return self.clients[client].send_message(
            system_prompt, user_prompt, message_history
        )
