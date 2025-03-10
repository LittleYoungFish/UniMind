"""
This module contains the Executor class that represents an agent executing tasks in a chat session.
It provides methods to interact with the OpenAI chat API and handle query execution.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict, field
from openai.types.chat.chat_completion import ChatCompletion


@dataclass
class ExecutorGenerationParams:
    """
    Dataclass to represent the generation parameters for the Executor class.
    None values represent parameters that are default to the API.
    """

    stop: Optional[str] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    frequency_penalty: Optional[float] = None
    max_completion_tokens: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ExecutorConfig:
    """
    Dataclass to represent the configuration parameters for the Executor class.
    """

    api_key: str
    model: str
    base_url: Optional[str] = None
    generation_params: ExecutorGenerationParams = field(
        default_factory=ExecutorGenerationParams
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        result = {
            "api_key": self.api_key,
            "model": self.model,
        }
        if self.base_url:
            result["base_url"] = self.base_url

        gen_params = self.generation_params.to_dict()
        if gen_params:
            result["generation_params"] = gen_params

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutorConfig":
        """Create configuration from dictionary."""
        gen_params = ExecutorGenerationParams()
        if "generation_params" in data:
            for key, value in data["generation_params"].items():
                if hasattr(gen_params, key):
                    setattr(gen_params, key, value)

        return cls(
            api_key=data["api_key"],
            model=data["model"],
            base_url=data.get("base_url"),
            generation_params=gen_params,
        )

    def save_to_file(self, filepath: str) -> None:
        """Save configuration to a JSON file."""
        with open(filepath, "w") as f:
            config_dict = self.to_dict()
            config_dict["api_key"] = "***"  # Masked for security
            json.dump(config_dict, f, indent=2)

    @classmethod
    def load_from_file(
        cls, filepath: str, api_key: Optional[str] = None
    ) -> "ExecutorConfig":
        """Load configuration from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)

        # If API key is provided, use it instead of the one in the file
        if api_key:
            data["api_key"] = api_key

        return cls.from_dict(data)

    @classmethod
    def from_env(cls) -> "ExecutorConfig":
        """Create configuration from environment variables."""
        load_dotenv()
        api_key = os.getenv("API_KEY", "")
        base_url = os.getenv("API_BASE_URL")
        model = os.getenv("MODEL", "gpt_4o_mini")

        return cls(api_key=api_key, base_url=base_url, model=model)


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
    config: ExecutorConfig
    client: OpenAI

    def __init__(
        self, prompt: str, config: Optional[ExecutorConfig] = None, model: str = None
    ):
        """
        Initialize the Executor class with a prompt and configuration.

        Parameters:
            prompt (str): The initial prompt for the executor.
            config (ExecutorConfig, optional): Configuration for the executor.
            model (str, optional): The model to use. If provided, overrides the model from config.

        Raises:
            ValueError: If the API key is not provided or the model is not specified.
        """
        self.prompt = prompt

        # Initialize with config if provided, otherwise load from env
        if config:
            self.config = config
        else:
            self.config = ExecutorConfig.from_env()

        # Override model if provided
        if model:
            self.model = model
        else:
            self.model = self.config.model

        if not self.config.api_key:
            raise ValueError("API key is required")

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)

    @classmethod
    def from_config_file(
        cls,
        prompt: str,
        config_file: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the Executor from a configuration file.

        Parameters:
            prompt (str): The initial prompt for the executor.
            config_file (str): Path to the configuration file.
            api_key (str, optional): API key to override the one in config file.
            model (str, optional): Model to override the one in config file.

        Returns:
            Executor: An initialized executor instance.
        """
        config = ExecutorConfig.load_from_file(config_file, api_key)
        if model:
            config.model = model
        return cls(prompt=prompt, config=config)

    @classmethod
    def from_params(
        cls,
        prompt: str,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        **generation_params,
    ):
        """
        Initialize the Executor with explicit parameters.

        Parameters:
            prompt (str): The initial prompt for the executor.
            api_key (str): The OpenAI API key.
            model (str): The model to use.
            base_url (str, optional): Base URL for API requests.
            **generation_params: Additional parameters for generation.

        Returns:
            Executor: An initialized executor instance.
        """
        gen_params = ExecutorGenerationParams()
        for key, value in generation_params.items():
            if hasattr(gen_params, key):
                setattr(gen_params, key, value)

        config = ExecutorConfig(
            api_key=api_key,
            model=model,
            base_url=base_url,
            generation_params=gen_params,
        )
        return cls(prompt=prompt, config=config)

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

        # Merge default generation params from config with override params
        merged_params = self.config.generation_params.to_dict()
        merged_params.update(generation_params)

        response: ChatCompletion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": query},
            ],
            model=self.model,
            **merged_params,
        )

        return ExecutionResult(
            response.choices[0].message.content,
            usage=ExecutionUsage(
                response.usage.prompt_tokens, response.usage.completion_tokens
            ),
        )

    def save_config(self, filepath: str) -> None:
        """Save the current configuration to a file."""
        self.config.save_to_file(filepath)
