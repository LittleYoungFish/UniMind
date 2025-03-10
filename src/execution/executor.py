"""
This module contains the Executor class that represents an agent executing tasks in a chat session.
It provides methods to interact with the OpenAI chat API and handle query execution.
"""

import os
import warnings
from openai import OpenAI
from dotenv import load_dotenv
from dataclasses import dataclass
from openai.types.chat.chat_completion import ChatCompletion


@dataclass
class ExecutionUsage:
    """
    Dataclass to represent the usage statistics of an execution response.
    """

    prompt: int
    completion: int


@dataclass
class ExecutionResult:
    """
    Dataclass to represent a result from the model execution.
    """

    content: str
    usage: ExecutionUsage

    def __str__(self):
        return f"<ExecutionResult> ({self.content[:50]})"


class Executor:
    """
    Class to represent an executor agent that processes queries through an LLM.
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
        Initialize the Executor class with a prompt.
        Loads environment variables and sets up the OpenAI client.
        Validates the API key and model.
        Defaults to GPT-4o-mini if no model is specified.

        Parameters:
            prompt (str): The initial prompt for the executor.

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

    def execute(self, query: str, **generation_params) -> ExecutionResult:
        """
        Executes the query against the specified model.

        Args:
            query (str): The user's query or task to execute.
            **generation_params: Additional parameters for the generation process.

        Returns:
           ExecutionResult: The response from the model.

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

        return ExecutionResult(
            response.choices[0].message.content,
            usage=ExecutionUsage(
                response.usage.prompt_tokens, response.usage.completion_tokens
            ),
        )
