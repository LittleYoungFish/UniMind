"""
Development of software using Agile methodology.
"""

import os
import json
import shutil
import readchar
from typing import Dict
from pathlib import Path
from context import Context
from execution import Agent
from rich.panel import Panel
from tool import get_all_tools
from prompt import agile_prompt
from rich import print as rich_print
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn


quality_assurance = Agent(
    "quality_assurance",
    "assure software quality",
    agile_prompt.QUALITY_ASSURANCE,
)
interactions_programmer = Agent(
    "interactions_programmer",
    "implement module interactions",
    agile_prompt.PROGRAMMER_INTERACTIONS,
    tools=get_all_tools(),
)
structure_programmer = Agent(
    "structure_programmer",
    "implement software structure",
    agile_prompt.PROGRAMMER_FRAMEWORK,
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
    output = os.path.abspath(".")
    context = Context(demand, output)

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
        context.set_document("demand_analysis", demand_analysis["content"])
        context.add_history("demand_analysis", demand_analysis)

        # Architecture step
        arch_task = progress.add_task("Building architecture...", total=1)
        architecture = architect.process(json.dumps(demand_analysis))
        architecture = json.loads(architecture["content"])
        progress.update(
            arch_task, completed=1, description="[bold green]Architecture created"
        )
        context.set_document("architecture", json.dumps(architecture, indent=4))
        context.add_history("architecture", architecture)

        # Implement modules
        modules = architecture["modules"]
        modules_task = progress.add_task("Implementing modules...", total=len(modules))
        module_subtasks = {}

        def process_module(module: Dict) -> tuple[str, Dict]:
            """
            Process a single module.

            Args:
                module: Module to process

            Returns:
                Tuple containing the module name and the implemented program
            """
            module_name: str = module["name"]
            subtask_id = progress.add_task(
                f"    Implementing module {module_name}...", total=1
            )
            module_subtasks[module_name] = subtask_id
            program = structure_programmer.process(json.dumps(module))
            for tool_call in program["tool_calls"]:
                if (
                    tool_call["tool"] == "create_file"
                    and tool_call["result"]["success"]
                ):
                    file_path = tool_call["args"]["path"]
                    file_content = tool_call["args"]["content"]
                    context.add_code(file_path, file_content)

            context.add_history(f"code_structure_{module_name}", program)
            progress.update(
                subtask_id,
                description=f"    [bold green]Module {module_name} implemented",
                completed=1,
            )

            return module_name, program

        # Execute module implementations in parallel
        completed_count = 0
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_module = {
                executor.submit(process_module, module): module for module in modules
            }
            for future in as_completed(future_to_module):
                _, _ = future.result()
                completed_count += 1
                progress.update(modules_task, completed=completed_count)

        for subtask_id in module_subtasks.values():
            progress.remove_task(subtask_id)
        progress.update(
            modules_task,
            description="[bold green]All modules implemented",
            completed=len(modules),
        )

        # Implement the interactions between modules
        interaction_task = progress.add_task("Checking module interactions...", total=1)
        interactions = interactions_programmer.process(
            json.dumps({"demand": demand, "modules": modules})
        )
        context.add_history("module_interactions", interactions)
        progress.update(
            interaction_task,
            completed=1,
            description="[bold green]Module interactions implemented",
        )

    rich_print(
        Panel(
            f"Development completed! Check your software in {output}",
            style="bold green",
            border_style="bold green",
            title="Success",
            title_align="center",
        )
    )

    return context.dump()


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
                f'The output directory "{output}" already exists. Do you want to delete its contents? (Y/n)',
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
        result = run_workflow(demand)

        with open("docs/development_record.json", "w") as f:
            f.write(json.dumps(result, indent=4))
    finally:
        os.chdir(initial_cwd)  # Restore original working directory

    return result
