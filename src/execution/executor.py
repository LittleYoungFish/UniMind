"""
This module contains the Executor class that represents an agent executing tasks in a chat session.
It provides methods to interact with the OpenAI chat API and handle query execution.
"""

import os
import json
from task import Task
from openai import OpenAI
from context import Context
from dotenv import load_dotenv
from prompt import DEFAULT_SYSTEM_MESSAGE
from tool import get_all_tools, execute_tool
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict, field
from openai.types.chat.chat_completion import ChatCompletion, ChatCompletionMessage


@dataclass
class GenerationParams:
    """
    Dataclass to represent the generation parameters for the Executor class.
    None values represent parameters that are default to the API.
    """

    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: Optional[List[Dict]] = None
    temperature: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ExecutorConfig:
    """
    Dataclass to represent the configuration parameters for the Executor class.
    """

    api_key: str
    default_model: str
    base_url: Optional[str] = None
    generation_params: GenerationParams = field(default_factory=GenerationParams)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        result = {
            "api_key": "REDACTED" if self.api_key else None,
            "default_model": self.default_model,
            "base_url": self.base_url,
            "generation_params": self.generation_params.to_dict(),
        }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutorConfig":
        """Create configuration from dictionary."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("API key is required, please set OPENAI_API_KEY")

        return cls(
            api_key=api_key,
            default_model=data["default_model"],
            base_url=data["base_url"],
            generation_params=GenerationParams(**data["generation_params"]),
        )

    @classmethod
    def from_env(cls) -> "ExecutorConfig":
        """Create configuration from environment variables."""
        load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("API key is required, please set OPENAI_API_KEY")

        base_url = os.getenv("OPENAI_BASE_URL")
        default_model = os.getenv("AM_DEFAULT_MODEL")

        max_tokens = os.getenv("AM_MAX_TOKENS")
        top_p = os.getenv("AM_TOP_P")
        temperature = os.getenv("AM_DEFAULT_TEMPERATURE")

        generation_params = GenerationParams(
            max_tokens=int(max_tokens) if max_tokens else None,
            top_p=float(top_p) if top_p else None,
            temperature=float(temperature) if temperature else None,
        )

        return cls(
            api_key=api_key,
            default_model=default_model,
            base_url=base_url,
            generation_params=generation_params,
        )


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
        self.config = config if config else ExecutorConfig.from_env()
        if not self.config.api_key:
            raise ValueError("API key is required")

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)

    @classmethod
    def from_env(cls) -> "Executor":
        """Create an executor from environment variables."""
        return cls(config=ExecutorConfig.from_env())

    def execute(self, task: Task, context: Context) -> Context:
        """
        Executes a task.

        Args:
            task: The Task instance containing the task description and metadata
            context: Contextual information

        Returns:
           Dict[str, Any]: The response from the model containing the generated text and usage statistics.

        Raises:
            ValueError: If an unsupported generation parameter is provided.
        """
        system_message = task.agent.background or DEFAULT_SYSTEM_MESSAGE
        model = task.agent.model or self.config.default_model
        query = task.input
        task.status = "in_progress"

        # Merge default generation params from config with override params
        merged_params = self.config.generation_params.to_dict()
        merged_params.update(task.agent.config or {})
        if task.agent.use_tool:
            merged_params["tools"] = get_all_tools()

        try:
            response: ChatCompletion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": query},
                ],
                model=model,
                **merged_params,
            )
            message: ChatCompletionMessage = response.choices[0].message

            if (
                message.tool_calls
                and len(message.tool_calls) > 0
                and message.tool_calls[0]
            ):
                try:
                    # Handle tool calls
                    tool_call = message.tool_calls[0]
                    func = tool_call.function

                    # Execute the tool function
                    tool_result = execute_tool(func.name, json.loads(func.arguments))
                except:
                    raise ValueError("Invalid tool call format")

            # Assemble the result from the response
            result = {
                "response": response.choices[0].message.content,
                "usage": ExecutionUsage(
                    prompt=response.usage.prompt_tokens,
                    completion=response.usage.completion_tokens,
                ),
            }

            task.set_result(result)

            # Update context with task result
            context[f"task_{task.get_name()}_result"] = result
            return context

        except Exception as e:
            task.set_failed(str(e))
            raise
