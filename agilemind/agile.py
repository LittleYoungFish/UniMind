"""
Development of software using Agile methodology.
"""

import os
import json
from pathlib import Path
from tool import get_all_tools
from prompt import agile_prompt
from execution import Agent, Runner

quality_assurance = Agent(
    "quality_assurance",
    "assure software quality",
    agile_prompt.QUALITY_ASSURANCE,
)
programmer = Agent(
    "programmer",
    "implement software",
    agile_prompt.PROGRAMMER,
    tools=get_all_tools(),
    handoffs=[quality_assurance],
)
quality_assurance.next_agent = programmer
architect = Agent(
    "architect",
    "create software architecture",
    agile_prompt.ARCHITECT,
    next_agent=programmer,
    save_path="docs/software_architecture.json",
)
demand_analyst = Agent(
    "demand_analyst",
    "analyze user demand",
    agile_prompt.DEMAND_ANALYST,
    next_agent=architect,
    save_path="docs/demand_analysis.md",
)


def dev(demand: str, output: str) -> dict:
    """
    Run the LLM-Agent workflow pipelines.

    Args:
        demand: User demand for the software
        output: Directory path to save the software

    Returns:
        Dictionary containing the software development process
    """
    Path(output).mkdir(parents=True, exist_ok=True)

    # Change current working directory to the output directory
    initial_cwd = os.getcwd()
    os.chdir(output)

    try:
        runner = Runner()
        result = runner.run(demand_analyst, demand, 5)

        with open("docs/trace.txt", "w") as f:
            f.write(json.dumps(result, indent=4))
    finally:
        os.chdir(initial_cwd)  # Restore original working directory

    return result
