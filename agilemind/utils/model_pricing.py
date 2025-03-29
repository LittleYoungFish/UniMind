"""
Module to store and manage LLM model pricing information.
"""

from enum import Enum
from typing import Dict
from dataclasses import dataclass
from rich import print as rich_print

# Set to track models that have already been warned about
_warned_models = set()


@dataclass
class ModelPrice:
    """Class for storing model pricing information."""

    # Input price in USD per 1000 tokens
    input_price: float
    # Output price in USD per 1000 tokens
    output_price: float
    # Human-readable model name
    name: str


class ModelPricing(Enum):
    """Enum for common LLM models and their pricing."""

    # OpenAI models
    GPT_4O_MINI = ModelPrice(0.00015, 0.0006, "GPT-4o Mini")
    GPT_4O = ModelPrice(0.0025, 0.01, "GPT-4o")

    # Anthropic models
    CLAUDE_3_7_SONNET_20250219 = ModelPrice(
        0.0033, 0.0165, "Claude 3.7 Sonnet 20250219"
    )

    # Deepseek models
    DEEPSEEK_V3 = ModelPrice(0.000272, 0.001088, "DeepSeek V3")
    DEEPSEEK_R1 = ModelPrice(0.000546, 0.002184, "DeepSeek R1")

    def known_models() -> list:
        """Return a list of known model names"""
        return [model.name for model in ModelPricing]


def calculate_cost(
    model: str, prompt_tokens: int, completion_tokens: int
) -> Dict[str, float]:
    """
    Calculate the cost for a given model and token usage.

    Args:
        model: The model to calculate pricing for
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens

    Returns:
        Dictionary with prompt_cost, completion_cost, and total_cost
    """
    # Format model name for comparison
    model = model.upper().replace("-", "_").replace(" ", "_")

    if model not in ModelPricing.known_models():
        if model not in _warned_models:
            rich_print(
                f"[yellow]Unknown price for model: {model}, using GPT-4o's price for reference.[/yellow]"
            )
            _warned_models.add(model)
        model = "GPT_4O"

    model_price = ModelPricing[model.upper()].value
    prompt_cost = model_price.input_price * (prompt_tokens / 1000)
    completion_cost = model_price.output_price * (completion_tokens / 1000)
    total_cost = prompt_cost + completion_cost

    return {
        "prompt_cost": prompt_cost,
        "completion_cost": completion_cost,
        "total_cost": total_cost,
    }
