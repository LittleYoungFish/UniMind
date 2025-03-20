"""
Agent module for creating agents that can process inputs, use tools, and hand off to other agents.
"""

import os
import json
import openai
from utils import retry
from context import Context
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
        self.save_path = save_path
        self.rounds = []  # Track information by round

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

    def process(self, context: Context, input_text: str) -> Dict:
        """
        Process the input using OpenAI API and return the agent's response.
        This method is decorated with retry to handle transient failures.

        Args:
            context: The context object
            input_text: The text input to process

        Returns:
            Dict containing the agent's response and any actions taken
        """
        return self._process_with_retry(context, input_text)

    @retry(
        exceptions=[
            openai.APIError,
            openai.APIConnectionError,
            openai.RateLimitError,
            openai.APITimeoutError,
            openai.InternalServerError,
            json.JSONDecodeError,
        ],
    )
    def _process_with_retry(self, context: Context, input_text: str) -> List[Dict]:
        """
        Internal method to process input with retry capabilities.
        This method is decorated with retry to handle transient failures.

        Args:
            context: The context object
            input_text: The text input to process

        Returns:
            List of dictionaries containing information for each round of interaction
        """
        messages = self._prepare_messages(input_text)

        # Initialize rounds tracking
        self.rounds = []
        current_round = {
            "input": input_text,
            "output": None,
            "tool_calls": None,
            "handoff": None,
        }

        # Add handoff agents as tools
        tools_with_handoffs = (
            self.tools.copy()
        )  # Create a copy to avoid modifying the original
        for agent in self.handoffs:
            tools_with_handoffs.append(
                {
                    "type": "function",
                    "function": {
                        "name": f"handoff_to_{agent.name}",
                        "description": f"Hand off the conversation to the {agent.name} agent. The agent is specialized in {agent.description}.",
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
            )

        round_number = 0

        # Continue conversation until no more tool calls or a handoff is requested
        while True:
            round_number += 1

            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools_with_handoffs if tools_with_handoffs else None,
                )
            except Exception:
                raise

            response_message = response.choices[0].message

            # Update current round with output
            current_round["output"] = response_message.content

            # Save the response if a save path is specified
            if self.save_path and response_message.content:
                self.save_response(response_message.content)

            # Check for handoff or tool calls
            handoff_requested = False
            current_round_tool_calls = []

            if hasattr(response_message, "tool_calls") and response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    tool_name = tool_call.function.name

                    # Check if this is a handoff
                    if tool_name.startswith("handoff_to_"):
                        target_agent_name = tool_name[len("handoff_to_") :]
                        for agent in self.handoffs:
                            if agent.name == target_agent_name:
                                current_round["handoff"] = agent.name
                                handoff_requested = True
                                break
                        if handoff_requested:
                            break
                    else:
                        # Execute the tool
                        args = json.loads(tool_call.function.arguments)
                        tool_result = execute_tool(context, tool_name, args)
                        current_tool_call = {
                            "tool": tool_name,
                            "args": args,
                            "result": tool_result,
                        }
                        current_round_tool_calls.append(current_tool_call)

                        # Add the tool call and result to messages for the next turn
                        messages.append(
                            {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": tool_call.id,
                                        "type": "function",
                                        "function": {
                                            "name": tool_name,
                                            "arguments": tool_call.function.arguments,
                                        },
                                    }
                                ],
                            }
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(tool_result),
                            }
                        )

            # Update current round with tool calls if any
            if current_round_tool_calls:
                current_round["tool_calls"] = current_round_tool_calls

            # Add the current round to rounds list
            self.rounds.append(current_round.copy())

            # Break the loop if no tool calls or handoff is requested
            if not current_round_tool_calls or handoff_requested:
                break

            # Prepare for next round - tool results become the new input
            next_input = f"Tool results: {json.dumps(current_round_tool_calls)}"
            current_round = {
                "input": next_input,
                "output": None,
                "tool_calls": None,
                "handoff": None,
            }

        # Check if there's a forced handoff via next_agent, which takes precedence over
        # any handoff the agent might have selected
        if self.next_agent:
            # Update the last round with the forced handoff
            self.rounds[-1]["handoff"] = self.next_agent.name

        return self.rounds

    def _prepare_messages(self, input_text: str) -> List[Dict]:
        """Prepare the message for the API call."""
        # Start with system instructions
        messages = [{"role": "system", "content": self.instructions}]
        # Add the current input
        messages.append({"role": "user", "content": input_text})

        return messages
