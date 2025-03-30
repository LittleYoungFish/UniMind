"""
Development of software using agile methodology.
"""

import os
import json
import shutil
import readchar
from pathlib import Path
from tool import get_tool
from typing import Optional
from execution import Agent
from context import Context
from rich.panel import Panel
from rich.align import Align
from prompt import agile_prompt
from rich.console import Console
from rich import print as rprint
from utils.window import LogWindow
from utils import load_config, extract_agent_llm_config

config = load_config()
console = Console()

prototype_builder = Agent(
    name="prototype_builder",
    description="Build prototype of the software",
    instructions=agile_prompt.PROTOTYPE_DEVELOPER,
    tools=[get_tool("write_file")],
    **extract_agent_llm_config("prototype", config),
)

all_agents = [prototype_builder]


def build_prototype(
    context: Context,
    window: LogWindow,
    demand: str,
    max_iterations: int = 5,
) -> dict:
    """
    Build a prototype of the software.

    Args:
        context (Context): Context object containing the software development process
        window (LogWindow): CLI window for displaying progress
        demand (str): User demand for the software
        max_iterations (int): Maximum number of iterations to run

    Returns:
        out: Dictionary containing the prototype development process
    """
    prototype_task = window.add_task("Developing prototype", status="running")

    prototype = prototype_builder.process(context, demand, max_iterations)

    window.update_task(prototype_task, status="pending")

    client_satisfied = False
    revision_count = 0
    feedback = ""
    while not client_satisfied and revision_count < max_iterations:
        window.hide()
        console.print(
            Panel(
                Align.center(
                    "The prototype has been developed. Please check the prototype and provide feedback. Are you satisfied with the prototype? (Y/n)"
                ),
                border_style="bold blue",
                title="Client Feedback",
            )
        )
        client_satisfied = readchar.readchar().lower() == "y"
        console.clear()

        if not client_satisfied:
            revision_count += 1
            previous_prototype = prototype
            feedback_template = (
                "Given client's demand: \n{demand}\n\n"
                "Previously the prototype is: \n{previous_prototype}\n\n"
                "The client has provided the following feedback for the prototype: \n{feedback}"
            )
            input_text = input("Please provide your feedback for the prototype: ")
            feedback += input_text + "\n"
            feedback_info = feedback_template.format(
                demand=demand,
                previous_prototype=previous_prototype,
                feedback=feedback,
            )

            window.show()
            window.update_task(prototype_task, status="running")
            prototype = prototype_builder.process(
                context, feedback_info, max_iterations
            )
            window.update_task(prototype_task, status="pending")

    window.complete_task(prototype_task)
    return prototype


def build_architecture(
    context: Context,
    window: LogWindow,
    demand: str,
    feedback: str,
    prototype: str,
    max_iterations: int = 5,
) -> dict:
    """
    Build a prototype of the software.

    Args:
        context (Context): Context object containing the software development process
        window (LogWindow): CLI window for displaying progress
        demand (str): User demand for the software
        feedback (str): Feedback from the client
        prototype (str): Final prototype of the software
        max_iterations (int): Maximum number of iterations to run

    Returns:
        out: Dictionary containing the prototype development process
    """


def run_workflow(
    demand: str,
    max_iterations: int = 5,
    model: Optional[str] = None,
) -> dict:
    """
    Run the LLM-Agent workflow pipelines.

    Args:
        demand (str): User demand for the software
        max_iterations (int): Maximum number of iterations to run
        model (str, Optional): String name of the model to use

    Returns:
        out: Dictionary containing the software development process
    """
    if model:
        for agent in all_agents:
            agent.set_model(model)

    output_dir = os.path.abspath(os.getcwd())
    context = Context(demand, output_dir)

    window = LogWindow(title="AgileMind Development")
    window.open()

    result = build_prototype(context, window, demand, max_iterations)

    window.close()

    return result


def dev(
    demand: str, output: str, model: Optional[str] = None, max_iterations: int = 5
) -> dict:
    """
    Run the LLM-Agent workflow pipelines.

    Args:
        demand (str): User demand for the software
        output (str): Directory path to save the software
        model (str, Optional): String name of the model to use
        max_iterations (int, Optional): Maximum number of iterations to run

    Returns:
        out: Dictionary containing the software development process
    """
    # If output dir exists, ask user whether to confirm purging it first
    if Path(output).exists():
        rprint(
            Panel(
                Align.center(
                    f'The output directory "{output}" already exists. Do you want to delete its contents? (Y/n)'
                ),
                border_style="bold red",
                title="Warning",
            )
        )

        confirm = readchar.readchar().lower()
        console.clear()

        if confirm != "y":
            return {"status": "cancelled"}

        # Purge the output directory
        shutil.rmtree(output)

    Path(output).mkdir(parents=True, exist_ok=True)
    Path(output, "docs").mkdir(parents=True, exist_ok=True)
    Path(output, "logs").mkdir(parents=True, exist_ok=True)

    # Change current working directory to the output directory
    initial_cwd = os.getcwd()
    os.chdir(output)

    try:
        result = run_workflow(demand, model=model, max_iterations=max_iterations)

        with open("logs/development_record.json", "w") as f:
            f.write(json.dumps(result, indent=4))
    finally:
        os.chdir(initial_cwd)  # Restore original working directory

    return result
