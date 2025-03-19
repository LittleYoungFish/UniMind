"""
Development of software using Agile methodology.
"""

import os
import json
import shutil
import readchar
from pathlib import Path
from execution import Agent
from rich.panel import Panel
from tool import get_all_tools
from prompt import agile_prompt
from rich import print as rich_print
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn


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
)
architect = Agent(
    "architect",
    "create software architecture",
    agile_prompt.ARCHITECT,
    save_path="docs/software_architecture.json",
)
demand_analyst = Agent(
    "demand_analyst",
    "analyze user demand",
    agile_prompt.DEMAND_ANALYST,
    save_path="docs/demand_analysis.md",
)


def run_workflow(
    demand: str,
    output: str,
    max_iterations: int = 5,
) -> dict:
    """
    Run the LLM-Agent workflow pipelines.

    Args:
        demand: User demand for the software
        output: Directory path to save the software

    Returns:
        Dictionary containing the software development process
    """
    result = {}

    with Progress(
        SpinnerColumn(finished_text="[bold green]\N{HEAVY CHECK MARK}"),
        TimeElapsedColumn(),
        TextColumn("[bold blue]{task.description}"),
    ) as progress:
        # Demand analysis step
        demand_task = progress.add_task("Analyzing user demand...", total=1)
        demand_analysis = demand_analyst.process(demand)
        progress.update(
            demand_task,
            completed=1,
            description="[bold green]Demand analysis completed",
        )
        result["demand_analysis"] = demand_analysis

        # Architecture step
        arch_task = progress.add_task("Building architecture...", total=1)
        architecture = architect.process(json.dumps(demand_analysis))
        # Convert the architecture from JSON format
        architecture = json.loads(architecture["content"])
        progress.update(
            arch_task, completed=1, description="[bold green]Architecture created"
        )
        result["architecture"] = architecture

        modules = architecture["modules"]

        # Create parent task for module implementation
        modules_task = progress.add_task("Implementing module...", total=len(modules))
        module_subtask = []

        for i, module in enumerate(modules):
            module_name = module["name"]

            module_subtask.append(
                progress.add_task(f"    Implementing module {module_name}...", total=1)
            )

            program = programmer.process(json.dumps(module))

            with open(f"docs/{module_name}.json", "w") as f:
                f.write(json.dumps(program, indent=4))

            result[module_name] = program

            # Mark the subtask as completed
            progress.update(
                module_subtask[-1],
                description=f"    [bold green]Module {module_name} implemented",
                completed=1,
            )

            # Update parent task completion count
            progress.update(modules_task, completed=i + 1)

        # Remove all subtasks
        for subtask in module_subtask:
            progress.remove_task(subtask)

        progress.update(
            modules_task,
            description="[bold green]All modules implemented",
            completed=len(modules),
        )

    abs_path = os.path.abspath(".")
    rich_print(
        Panel(
            f"Development completed! Check your software in {abs_path}",
            style="bold green",
            border_style="bold green",
            title="Success",
            title_align="center",
        )
    )

    return result


def dev(
    demand: str,
    output: str,
) -> dict:
    """
    Run the LLM-Agent workflow pipelines.

    Args:
        demand: User demand for the software
        output: Directory path to save the software

    Returns:
        Dictionary containing the software development process
    """
    # If output dir exists, ask user whether to confirm purging it first
    if Path(output).exists():
        rich_print(
            Panel(
                "The output directory already exists. Do you want to delete its contents? (Y/n)",
                border_style="bold red",
                title="Warning",
                title_align="center",
            )
        )

        confirm = readchar.readchar().lower()
        if confirm != "y":
            return {"status": "cancelled"}

        # Purge the output directory
        shutil.rmtree(output)

    Path(output).mkdir(parents=True, exist_ok=True)

    # Change current working directory to the output directory
    initial_cwd = os.getcwd()
    os.chdir(output)

    try:
        result = run_workflow(demand, output)

        with open("docs/trace.txt", "w") as f:
            f.write(json.dumps(result, indent=4))
    finally:
        os.chdir(initial_cwd)  # Restore original working directory

    return result
