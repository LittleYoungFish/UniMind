"""
This module contains the Executor class that represents an agent executing tasks in a chat session.
It provides methods to interact with the OpenAI chat API and handle query execution.
"""

import json
from task import Task
from enum import Enum
from openai import OpenAI
from context import Context
from prompt import DEFAULT_SYSTEM_MESSAGE
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict, field
from openai.types.chat.chat_completion import ChatCompletion


class AgentType(Enum):
    """Enumeration of available agent types in the pipeline."""

    CUSTOM = "custom"
    # TODO Add agent type


@dataclass
class ExecutorGenerationParams:
    """
    Dataclass to represent the generation parameters for the Executor class.
    None values represent parameters that are default to the API.
    """

    stop: Optional[str] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: Optional[List[Dict]] = None
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
    system_message: Optional[str] = None
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

        if self.system_message:
            result["system_message"] = self.system_message

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
            system_message=data.get("system_message"),
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


@dataclass
class ExecutionUsage:
    """
    Dataclass to represent the usage statistics of an execution response.
    """

    prompt: int
    completion: int


class Executor:
    """
    Class to represent an executor agent that processes queries through an LLM.
    """

    config: ExecutorConfig
    client: OpenAI

    def __init__(self, config: Optional[ExecutorConfig] = None):
        """
        Initialize the Executor class with a prompt and configuration.

        Parameters:
            prompt (str): The initial prompt for the executor.
            config (ExecutorConfig, optional): Configuration for the executor.
            model (str, optional): The model to use. If provided, overrides the model from config.

        Raises:
            ValueError: If the API key is not provided or the model is not specified.
        """

        # Initialize with config if provided, otherwise load from env
        if config:
            self.config = config
        else:
            self.config = ExecutorConfig.from_env()

        if not self.config.api_key:
            raise ValueError("API key is required")

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)

    def execute(
        self, task: Task, context: Context, **generation_params
    ) -> Dict[str, Any]:
        """
        Executes a task.

        Args:
            task: The Task instance containing the task description and metadata
            context: Contextual information
            **generation_params: Additional parameters for the generation process

        Returns:
           Dict[str, Any]: The response from the model containing the generated text and usage statistics.

        Raises:
            ValueError: If an unsupported generation parameter is provided.
        """
        system_message = task.background or DEFAULT_SYSTEM_MESSAGE
        query = task.description
        task.status = "in_progress"

        # Merge default generation params from config with override params
        merged_params = self.config.generation_params.to_dict()
        merged_params.update(generation_params)

        # Prepare context for the message
        context_content = ""
        if context:
            context_content = "Context:\n" + "\n".join(
                [f"{k}: {v}" for k, v in context.items()]
            )
            if context_content:
                query = f"{context_content}\n\nQuery: {query}"

        try:
            response: ChatCompletion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": query},
                ],
                model=self.config.model,
                **merged_params,
            )

            # If tool calls are present, extract them from response
            if response.tool_calls:
                task.metadata["tool_calls"] = response.tool_calls

            # Assemble the result from the response
            result = {
                "response": response.choices[0].message.content,
                "usage": ExecutionUsage(
                    prompt=response.usage.prompt_tokens,
                    completion=response.usage.completion_tokens,
                ),
            }

            task.set_result(result)
            return result

        except Exception as e:
            task.set_failed(str(e))
            raise
