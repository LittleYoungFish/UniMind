"""
Development of software using agile methodology.
"""

import os
import json
import shutil
import readchar
from pathlib import Path
from rich.panel import Panel
from rich.align import Align
from rich.console import Console
from rich import print as rprint
from agilemind.tool import get_tool
from agilemind.execution import Agent
from agilemind.context import Context
from typing import Dict, List, Optional
from agilemind.prompt import agile_prompt
from concurrent.futures import ThreadPoolExecutor, as_completed
from agilemind.utils import (
    LogWindow,
    load_config,
    create_file_tree,
    extract_agent_llm_config,
    convert_json_to_markdown,
)

config = load_config()
console = Console()

prototype_builder = Agent(
    name="prototype_builder",
    description="Build prototype of the software",
    instructions=agile_prompt.PROTOTYPE_DEVELOPER,
    tools=[get_tool("write_file")],
    **extract_agent_llm_config("prototype", config),
)
architect = Agent(
    name="architect",
    description="Design architecture of the software",
    instructions=agile_prompt.ARCHITECT,
    tools=[get_tool("write_file")],
    **extract_agent_llm_config("architecture", config),
)
developer = Agent(
    name="developer",
    description="Implement code for the software",
    instructions=agile_prompt.DEVELOPER,
    tools=[get_tool("write_file")],
    **extract_agent_llm_config("programming", config),
)

all_agents = [prototype_builder, architect, developer]


def build_prototype(
    context: Context,
    window: LogWindow,
    demand: str,
    max_iterations: int = 5,
) -> tuple["str", "str"]:
    """
    Build a prototype of the software.

    Args:
        context (Context): Context object containing the software development process
        window (LogWindow): CLI window for displaying progress
        demand (str): User demand for the software
        max_iterations (int): Maximum number of iterations to run

    Returns:
        out: Tuple of feedback and prototype
    """
    window.log("Developing prototype of the software...")

    prototype_task = window.add_task("Developing prototype", status="running")

    prototype_builder.process(context, demand, max_iterations)

    if not os.path.isfile("docs/prototype.html"):
        print("Critical: Prototype file not found")
        raise FileNotFoundError("Prototype file not found")
    with open("docs/prototype.html", "r") as f:
        prototype = f.read()

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
            prototype_builder.process(context, feedback_info, max_iterations)
            window.update_task(prototype_task, status="pending")

            with open("docs/prototype.html", "r") as f:
                prototype = f.read()

    window.show()
    window.complete_task(prototype_task)

    return feedback, prototype


def build_architecture(
    context: Context,
    window: LogWindow,
    demand: str,
    feedback: str,
    prototype: str,
    max_iterations: int = 5,
) -> tuple[List, str]:
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
        out: Tuple of code file list and architecture information
    """
    window.log("Designing architecture of the software...")

    architecture_task = window.add_task("Developing architecture", status="running")
    demand_info = agile_prompt.FEEDBACK_TEMPLATE.format(
        raw_demand=demand, feedback=feedback, prototype=prototype
    )

    architect.process(context, demand_info, max_iterations)

    if not os.path.isfile("logs/architecture.json"):
        print("Critical: Architecture file not found")
        raise FileNotFoundError("Architecture file not found")
    with open("logs/architecture.json", "r") as f:
        json_info: Dict = json.load(f)

    md_info = json_info.copy()
    code_file_list_md = create_file_tree(json_info["code_file_list"])
    md_info["code_file_list"] = code_file_list_md
    architecture_md = convert_json_to_markdown(
        "introduction",
        "code_file_list",
        "class_structure",
        "call_flow",
        data=md_info,
        title="Software System Design",
        code_languages={
            "code_file_list": "plaintext",
            "class_structure": "mermaid",
            "call_flow": "mermaid",
        },
    )
    with open("docs/architecture.md", "w") as f:
        f.write(architecture_md)

    window.complete_task(architecture_task)
    return json_info.get("code_file_list", []), architecture_md


def implement_code(
    context: Context,
    window: LogWindow,
    code_file_list: List[str],
    architecture: str,
    max_iterations: int = 5,
) -> None:
    """
    Implement the code for the software.

    Args:
        context (Context): Context object containing the software development process
        window (LogWindow): CLI window for displaying progress
        code_file_list (List[str]): List of code files to implement
        architecture (str): Architecture information of the software
        max_iterations (int): Maximum number of iterations to run

    Returns:
        None
    """
    window.log("Implementing code for the software...")

    code_task = window.add_task("Implementing code", status="running")

    with ThreadPoolExecutor() as executor:
        code_tasks = [
            executor.submit(
                developer.process,
                context,
                agile_prompt.DEVELOPING_TEMPLATE.format(
                    architecture=architecture, file_path=file
                ),
                max_iterations,
            )
            for file in code_file_list
        ]
        for task in as_completed(code_tasks):
            task.result()

    window.log("Code implementation completed.")
    window.complete_task(code_task)

    return


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

    window.log("Starting the software development process...")

    feedback, prototype = build_prototype(context, window, demand, max_iterations)
    file_list, architecture = build_architecture(
        context, window, demand, feedback, prototype, max_iterations
    )

    implement_code(context, window, file_list, architecture, max_iterations)

    window.log("Software development process completed. Exiting...")
    window.close()

    return context.dump()


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
