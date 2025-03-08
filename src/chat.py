"""
Initialize different agents.
"""

import os
import warnings
from openai import OpenAI
from dotenv import load_dotenv
from dataclasses import dataclass
from openai.types.chat.chat_completion import ChatCompletion


@dataclass
class Usage:
    """
    Dataclass to represent the usage statistics of a chat model response.
    """

    prompt: int
    completion: int


@dataclass
class Response:
    """
    Dataclass to represent a response from the chat model.
    """

    content: str
    usage: Usage

    def __str__(self):
        return f"<Response> ({self.content[:50]})"


class Role:
    """
    Class to represent an agent role in a chat session.
    """

    model: str
    prompt: str

    ALLOWED_GEN_PARAM = [
        "n",
        "stop",
        "top_p",
        "max_tokens",
        "temperature",
        "frequency_penalty",
        "max_completion_tokens",
    ]

    def __init__(self, prompt: str):
        """
        Initialize the Role class with a prompt.
        Loads environment variables and sets up the OpenAI client.
        Validates the API key and model.
        Defaults to GPT-4o-mini if no model is specified.

        Parameters:
            prompt (str): The initial prompt for the chat session.

        Raises:
            ValueError: If the API key is not provided or the model is not specified.
        """

        is_env_loaded = load_dotenv()

        api_key = os.getenv("API_KEY", "")
        base_url = os.getenv("API_BASE_URL", None) or None
        model = os.getenv("MODEL", None) or None
        if not is_env_loaded or not api_key:
            raise ValueError("Please provide environment variables in .env file")
        if not model:
            warnings.warn("Model not specified, using GPT-4o-mini by default")
            model = "gpt_4o_mini"

        self.client = OpenAI(api_key=api_key, base_url=base_url)

        self.prompt = prompt
        self.model = model

    def chat(self, query: str, **generation_params) -> Response:
        """
        Handles the chat interaction with the specified model.

        Args:
            query (str): The user's query or message.
            **generation_params: Additional parameters for the generation process.

        Returns:
           Response: The response from the model.

        Raises:
            ValueError: If an unsupported generation parameter is provided.
        """
        for param in generation_params.keys():
            if param not in self.ALLOWED_GEN_PARAM:
                raise ValueError(f"Generation param {param} not implemented yet")

        response: ChatCompletion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": query},
            ],
            model=self.model,
            **generation_params,
        )

        return Response(
            response.choices[0].message.content,
            usage=Usage(response.usage.prompt_tokens, response.usage.completion_tokens),
        )
