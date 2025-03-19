"""
Agent module for creating agents that can process inputs, use tools, and hand off to other agents.
"""

import os
import json
import openai
from utils import retry
from tool import execute_tool
from dotenv import load_dotenv
from typing import List, Optional, Dict


load_dotenv()

client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL"),
)


class Agent:
    """
    An agent that can perform tasks based on instructions and use tools or hand off to other agents.

    Agents can process inputs according to their instructions, use tools to perform
    actions, or hand off to other specialized agents when appropriate.
    """

    def __init__(
        self,
        name: str,
        description: str,
        instructions: str,
        tools: Optional[List[Dict[str, str]]] = None,
        handoffs: Optional[List["Agent"]] = None,
        next_agent: Optional["Agent"] = None,  # Added next_agent for forced handoff
        model: str = "gpt-4o-mini",
        save_path: Optional[str] = None,  # Path to save agent responses
    ):
        """
        Initialize an Agent instance.

        Args:
            name: The name of the agent. Should be unique, lowercase, and without spaces.
            description: Brief description of what the agent does
            instructions: Instructions that define the agent's behavior.
            tools: Optional list of tools the agent can use.
            handoffs: Optional list of agents this agent can hand off to.
            next_agent: Optional next agent for forced handoff regardless of the agent's decision.
            model: OpenAI model to use for this agent
            save_path: Optional path to save agent's responses for documentation purposes
        """
        self.name = name
        self.description = description
        self.instructions = instructions
        self.tools = tools or []
        self.handoffs = handoffs or []
        self.next_agent = next_agent  # Store the next agent for forced handoff
        self.model = model
        self.history = []
        self.save_path = save_path

    def __repr__(self) -> str:
        """Return string representation of the Agent."""
        return f"Agent(name='{self.name}')"

    def get_available_tools(self) -> List[Dict[str, str]]:
        """Return the list of tools available to this agent."""
        return self.tools

    def get_available_handoffs(self) -> List["Agent"]:
        """Return the list of agents this agent can hand off to."""
        return self.handoffs

    def save_response(self, response_content: str) -> None:
        """
        Save the agent's response to the specified path.

        Args:
            response_content: The content to save to the file
        """
        if not self.save_path:
            return

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)

        # Append to file if it exists, otherwise create it
        with open(self.save_path, "a") as f:
            f.write(response_content + "\n\n")

    def process(self, input_text: str) -> Dict:
        """
        Process the input using OpenAI API and return the agent's response.
        This method is decorated with retry to handle transient failures.

        Args:
            input_text: The text input to process

        Returns:
            Dict containing the agent's response and any actions taken
        """
        return self._process_with_retry(input_text)

    @retry(
        exceptions=[
            openai.APIError,
            openai.APIConnectionError,
            openai.RateLimitError,
            openai.APITimeoutError,
            openai.InternalServerError,
        ],
    )
    def _process_with_retry(self, input_text: str) -> Dict:
        """
        Internal method to process input with retry capabilities.
        This method is decorated with retry to handle transient failures.

        Args:
            input_text: The text input to process

        Returns:
            Dict containing the agent's response and any actions taken
        """
        messages = self._prepare_messages(input_text)

        # Add handoff agents as tools
        for agent in self.handoffs:
            self.tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": f"handoff_to_{agent.name}",
                        "description": f"Hand off the conversation to the {agent.name} agent. The agent is specialized in {agent.description}.",
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
            )

        # Call OpenAI API
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools if self.tools else None,
            )
        except Exception as e:
            raise

        response_message = response.choices[0].message
        self.history.append({"role": "user", "content": input_text})
        self.history.append(
            {"role": "assistant", "content": response_message.content or ""}
        )

        result = {
            "content": response_message.content,
            "tool_calls": None,
            "handoff": None,
        }

        # Save the response if a save path is specified
        if self.save_path and response_message.content:
            self.save_response(response_message.content)

        # Handle tool calls
        if hasattr(response_message, "tool_calls") and response_message.tool_calls:
            result["tool_calls"] = []
            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name

                # Check if this is a handoff
                if tool_name.startswith("handoff_to_"):
                    target_agent_name = tool_name[len("handoff_to_") :]
                    for agent in self.handoffs:
                        if agent.name == target_agent_name:
                            result["handoff"] = agent
                            break
                else:
                    # Execute the tool
                    args = json.loads(tool_call.function.arguments)
                    tool_result = execute_tool(tool_name, args)
                    result["tool_calls"].append(
                        {"tool": tool_name, "args": args, "result": tool_result}
                    )

        # Check if there's a forced handoff via next_agent, which takes precedence over
        # any handoff the agent might have selected
        if self.next_agent:
            result["handoff"] = self.next_agent

        return result

    def _prepare_messages(self, input_text: str) -> List[Dict]:
        """Prepare the message history for the API call."""
        # Start with system instructions
        messages = [{"role": "system", "content": self.instructions}]
        # Add conversation history
        messages.extend(self.history)
        # Add the current input
        messages.append({"role": "user", "content": input_text})

        return messages
