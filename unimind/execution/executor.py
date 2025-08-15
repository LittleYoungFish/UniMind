"""
This module contains the Executor class that represents an agent executing tasks in a chat session.
It provides methods to interact with the OpenAI chat API and handle query execution.
"""

import json
from openai import OpenAI
from typing import Optional
from unimind.task import Task
from dataclasses import dataclass
from .config import ExecutorConfig
from unimind.context import Context
from unimind.prompt import DEFAULT_SYSTEM_MESSAGE
from unimind.tool import get_all_tools, execute_tool
from openai.types.chat.chat_completion import ChatCompletion, ChatCompletionMessage


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

        # 配置代理设置
        import httpx
        import os
        
        # 获取代理配置
        http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
        https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
        
        # 创建HTTP客户端（支持代理）
        http_client = None
        if http_proxy or https_proxy:
            # 优先使用http代理，避免SSL协议问题
            proxy_url = http_proxy or https_proxy
            
            # 确保代理URL使用http协议
            if proxy_url and proxy_url.startswith('https://'):
                proxy_url = proxy_url.replace('https://', 'http://')
            
            try:
                http_client = httpx.Client(
                    proxy=proxy_url,
                    timeout=60.0,
                    follow_redirects=True,
                    verify=False  # 跳过SSL验证以避免代理SSL问题
                )
            except Exception as e:
                # 如果代理失败，使用直连
                print(f"代理设置失败，使用直连: {e}")
                http_client = None
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=self.config.api_key, 
            base_url=self.config.base_url,
            http_client=http_client
        )

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
