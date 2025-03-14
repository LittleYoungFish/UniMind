import json
from pathlib import Path
from prompt import waterfall_prompt
from execution import Agent, Runner


demand_analyst = Agent(
    "demand_analyst",
    "analyze user demand",
    waterfall_prompt.DEMAND_ANALYST_PROMPT,
)
architect = Agent(
    "architect",
    "create software architecture",
    waterfall_prompt.ARCHITECT_PROMPT,
    handoffs=[demand_analyst],
)
programmer = Agent(
    "programmer",
    "implement software",
    waterfall_prompt.PROGRAMER_PROMPT,
    handoffs=[architect],
)
quality_assurance = Agent(
    "quality_assurance",
    "assure software quality",
    waterfall_prompt.QUALITY_ASSURANCE_PROMPT,
    handoffs=[programmer],
)


def dev(user_demand: str, output_dir: str) -> dict:
    """
    Run the LLM-Agent workflow pipelines.

    Args:
        user_demand: User demand for the software
        output_dir: Directory path to save the software

    Returns:
        Dictionary containing the software development process
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    runner = Runner()
    result = runner.run(demand_analyst, user_demand, 5)

    with open(f"{output_dir}/output.txt", "w") as f:
        f.write(json.dumps(result, indent=4))

    return result
