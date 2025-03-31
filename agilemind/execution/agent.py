"""
Agent module for creating agents that can process inputs, use tools, and hand off to other agents.
"""

import os
import json
import openai
from dotenv import load_dotenv
from .config import GenerationParams
from agilemind.context import Context
from agilemind.tool import execute_tool
from typing import List, Optional, Dict, Union
from agilemind.utils import retry, calculate_cost, clean_json_string


load_dotenv()


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
        generation_params: Optional[Union[GenerationParams, Dict]] = None,
        llm_base_url: Optional[str] = None,
        llm_api_key: Optional[str] = None,
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
            generation_params: Optional parameters for the model generation
            llm_base_url: Optional base URL for the OpenAI API
            llm_api_key: Optional API key for the OpenAI API
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
        self.generation_params = generation_params

        if isinstance(generation_params, dict):
            self.generation_params = GenerationParams(**generation_params)

        self.client = openai.OpenAI(
            api_key=llm_api_key or os.getenv("OPENAI_API_KEY"),
            base_url=llm_base_url or os.getenv("OPENAI_API_BASE_URL"),
        )

    def __repr__(self) -> str:
        """Return string representation of the Agent."""
        return f"Agent(name='{self.name}')"

    def get_available_tools(self) -> List[Dict[str, str]]:
        """Return the list of tools available to this agent."""
        return self.tools

    def get_available_handoffs(self) -> List["Agent"]:
        """Return the list of agents this agent can hand off to."""
        return self.handoffs

    def set_model(self, model: str) -> None:
        """
        Set the model to use for this agent.

        Args:
            model (str): The model to use
        """
        self.model = model

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

    def process(
        self, context: Context, input_text: str, max_iterations: int = None
    ) -> List[Dict]:
        """
        Process the input using OpenAI API and return the agent's response.
        This method is decorated with retry to handle transient failures.

        Args:
            context: The context object
            input_text: The text input to process
            max_iterations: Maximum number of interaction rounds (None means no limit)

        Returns:
            Dict containing the agent's response and any actions taken
        """
        result = self._process_with_retry(context, input_text, max_iterations)
        context.add_history(self.name, result.copy())
        return result

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
    def _process_with_retry(
        self, context: Context, input_text: str, max_iterations: int = None
    ) -> List[Dict]:
        """
        Internal method to process input with retry capabilities.
        This method is decorated with retry to handle transient failures.

        Args:
            context: The context object
            input_text: The text input to process
            max_iterations: Maximum number of interaction rounds (None means no limit)

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
            "token_usage": None,
            "cost": None,  # Add cost field to track costs per round
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
                        "description": f"Hand off to the {agent.name}, who is specialized in {agent.description}.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "instructions": {
                                    "type": "string",
                                    "description": "Instructions for that character to follow.",
                                }
                            },
                        },
                    },
                }
            )

        round_number = 0

        # Continue conversation until no more tool calls or a handoff is requested
        # or until max_iterations is reached (if specified)
        while max_iterations is None or round_number < max_iterations:
            round_number += 1

            try:
                print(f"Debug: {self.name} processing round {round_number}...")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools_with_handoffs if tools_with_handoffs else None,
                    **(
                        self.generation_params.to_dict()
                        if self.generation_params
                        else {}
                    ),
                )
                print("Debug: Response received.")
            except Exception as e:
                print(f"Error: {e}")
                raise

            response_message = response.choices[0].message

            # Update current round with output
            current_round["output"] = response_message.content

            # Record token usage with enhanced details
            if hasattr(response, "usage") and response.usage:
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens

                # Record token usage
                current_round["token_usage"] = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

                # Calculate cost using the model_pricing utility
                cost_info = calculate_cost(
                    model=self.model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )

                # Record cost information
                current_round["cost"] = cost_info

                # Update token usage in context with detailed information
                context.update_token_usage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    agent_name=self.name,
                    round_number=round_number,
                    model=self.model,
                )

                # Update cost information in context
                context.update_cost(
                    prompt_cost=cost_info["prompt_cost"],
                    completion_cost=cost_info["completion_cost"],
                    agent_name=self.name,
                    round_number=round_number,
                    model=self.model,
                )

            # Save the response if a save path is specified
            if self.save_path and response_message.content:
                if self.save_path.endswith(".json"):
                    self.save_response(clean_json_string(response_message.content))
                else:
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
                        args = json.loads(tool_call.function.arguments)
                        instruction = args.get("instructions", "")
                        # TODO: Add support for handoff instructions

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
                                "content": response_message.content,
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
            # or if we've reached the maximum number of iterations
            if (
                not current_round_tool_calls
                or handoff_requested
                or (max_iterations is not None and round_number >= max_iterations)
            ):
                break

            # Prepare for next round - tool results become the new input
            next_input = f"Tool results: {json.dumps(tool_result)}"
            current_round = {
                "input": next_input,
                "output": None,
                "tool_calls": None,
                "handoff": None,
                "token_usage": None,
            }

        # Check if there's a forced handoff via next_agent, which takes precedence over
        # any handoff the agent might have selected
        if self.next_agent:
            # Update the last round with the forced handoff
            self.rounds[-1]["handoff"] = self.next_agent.name

        return self.rounds

    def _prepare_messages(self, input_text: str) -> List[Dict]:
        """Prepare the message for the API call."""
        return [
            {"role": "system", "content": self.instructions},
            {"role": "user", "content": input_text},
        ]
