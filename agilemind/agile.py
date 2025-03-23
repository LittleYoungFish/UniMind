"""
Development of software using Agile methodology.
"""

import os
import json
import time
import shutil
import readchar
from typing import Dict
from pathlib import Path
from context import Context
from execution import Agent
from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from rich.box import ROUNDED
from utils import format_cost
from datetime import timedelta
from tool import get_all_tools
from prompt import agile_prompt
from rich import print as rich_print
from execution import deterministic_generation
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn


quality_assurance = Agent(
    "quality_assurance",
    "assure software quality",
    agile_prompt.QUALITY_ASSURANCE,
    generation_params=deterministic_generation,
)
logic_programmer = Agent(
    "logic_programmer",
    "implement software logic",
    agile_prompt.PROGRAMMER_LOGIC,
    tools=get_all_tools("file_system", "development"),
    generation_params=deterministic_generation,
)
interactions_programmer = Agent(
    "interactions_programmer",
    "implement module interactions",
    agile_prompt.PROGRAMMER_INTERACTIONS,
    tools=get_all_tools("file_system", "development"),
    generation_params=deterministic_generation,
)
structure_programmer = Agent(
    "structure_programmer",
    "implement software structure",
    agile_prompt.PROGRAMMER_FRAMEWORK,
    tools=get_all_tools("file_system", "development"),
    generation_params=deterministic_generation,
)
architect = Agent(
    "architect",
    "create software architecture",
    agile_prompt.ARCHITECT,
    save_path="docs/software_architecture.json",
    generation_params=deterministic_generation,
)
demand_analyst = Agent(
    "demand_analyst",
    "analyze user demand",
    agile_prompt.DEMAND_ANALYST,
    save_path="docs/demand_analysis.md",
    generation_params=deterministic_generation,
)


def run_workflow(
    demand: str,
    max_iterations: int = 5,
) -> dict:
    """
    Run the LLM-Agent workflow pipelines.

    Args:
        demand: User demand for the software
        max_iterations: Maximum number of iterations for each agent

    Returns:
        Dictionary containing the software development process
    """
    output = os.path.abspath(".")
    context = Context(demand, output)
    start_time = time.time()

    with Progress(
        SpinnerColumn(finished_text="[bold green]\N{HEAVY CHECK MARK}"),
        TimeElapsedColumn(),
        TextColumn("[bold blue]{task.description}"),
    ) as progress:
        # Demand analysis step
        demand_task = progress.add_task("Analyzing user demand...", total=1)
        demand_analysis = demand_analyst.process(context, demand, max_iterations)
        progress.update(
            demand_task,
            completed=1,
            description="[bold green]Demand analysis completed",
        )
        context.set_document("demand_analysis", demand_analysis[-1]["output"])
        context.add_history("demand_analysis", demand_analysis)

        # Architecture step
        arch_task = progress.add_task("Building architecture...", total=1)
        architecture = architect.process(
            context, json.dumps(demand_analysis), max_iterations
        )
        context.add_history("architecture", architecture)
        architecture = json.loads(architecture[-1]["output"])
        progress.update(
            arch_task, completed=1, description="[bold green]Architecture created"
        )
        context.set_document("architecture", json.dumps(architecture, indent=4))

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
            program_structure = structure_programmer.process(
                context, json.dumps(module), max_iterations
            )

            context.add_history(f"code_structure_{module_name}", program_structure)
            progress.update(
                subtask_id,
                description=f"    [bold green]Module {module_name} implemented",
                completed=1,
            )

            return module_name, program_structure

        # Execute module implementations in parallel
        completed_count = 0
        with ThreadPoolExecutor() as executor:
            future_to_module = {
                executor.submit(process_module, module): module for module in modules
            }
            for future in as_completed(future_to_module):
                _, _ = future.result()
                completed_count += 1
                progress.update(
                    modules_task,
                    description=(
                        ("[bold green]" if completed_count == len(modules) else "")
                        + f"{completed_count}/{len(modules)} modules implemented"
                    ),
                    completed=completed_count,
                )

        for subtask_id in module_subtasks.values():
            progress.remove_task(subtask_id)

        # Implement the interactions between modules
        interaction_task = progress.add_task("Checking module interactions...", total=1)
        module_interactions = interactions_programmer.process(
            context,
            json.dumps({"demand": demand, "modules": modules}),
            max_iterations,
        )
        context.add_history("module_interactions", module_interactions)
        progress.update(
            interaction_task,
            completed=1,
            description="[bold green]Module interactions implemented",
        )

        # Implement the logic of every file in parallel
        files = list(context.code.uptodated.keys())
        logic_task = progress.add_task("Implementing code logic...", total=len(files))
        completed_count = 0

        def process_code_logic(file: str) -> tuple[str, Dict]:
            """
            Process the logic of a single file.

            Args:
                file: File to process

            Returns:
                Tuple containing the file name and the implemented logic
            """
            # Prepare the input file data in XML format
            file_data = context.code.uptodated[file]
            xml_data = f"<path>{file}</path>\n<code>{file_data}</code>"

            logic = logic_programmer.process(context, xml_data, max_iterations)
            context.add_history(f"code_logic_{file}", logic)

            return file, logic

        # Execute code logic implementations in parallel
        with ThreadPoolExecutor() as executor:
            future_to_file = {
                executor.submit(process_code_logic, file): file for file in files
            }
            for future in as_completed(future_to_file):
                _, _ = future.result()
                completed_count += 1
                progress.update(
                    logic_task,
                    description=(
                        ("[bold green]" if completed_count == len(files) else "")
                        + f"Logic of {completed_count}/{len(files)} files implemented"
                    ),
                    completed=completed_count,
                )

    # Software information
    total_time = time.time() - start_time
    time_str = str(timedelta(seconds=int(total_time)))
    software_name = architecture["name"]
    module_count = len(modules)
    file_count = len(context.code.uptodated.keys())
    lines_of_code = sum(len(f.split("\n")) for f in context.code.uptodated.values())
    doc_count = len(context.document)
    doc_lines = sum(len(doc.split("\n")) for doc in context.document.values())

    # Get token usage info
    token_usage = context.token_usage.to_dict()
    total_prompt_tokens = token_usage["total"]["prompt_tokens"]
    total_completion_tokens = token_usage["total"]["completion_tokens"]
    total_tokens = token_usage["total"]["total_tokens"]

    # Get cost info
    cost_info = context.cost.to_dict()
    total_prompt_cost = cost_info["total"]["prompt_cost"]
    total_completion_cost = cost_info["total"]["completion_cost"]
    total_cost = cost_info["total"]["total_cost"]

    # Create project info table with expanded width
    project_table = Table(
        title="Project Information",
        expand=True,
        padding=(0, 2),
        box=ROUNDED,
        title_justify="left",
    )
    project_table.add_column("Project", style="bold cyan")
    project_table.add_column("Development Time", style="bold yellow")
    project_table.add_column("Project Directory", style="bold green")
    project_table.add_row(software_name, time_str, output)

    # Second row of information
    details_table = Table(
        title="Development Details",
        expand=True,
        padding=(0, 2),
        box=ROUNDED,
        title_justify="left",
        show_header=False,
        show_lines=True,
    )
    details_table.add_row(
        f"Modules Created: [bold yellow]{module_count}[/bold yellow]",
        f"Files Created: [bold blue]{file_count}[/bold blue]",
        f"Documents Created: [bold green]{doc_count}[/bold green]",
    )
    details_table.add_row(
        f"Average files per module: [bold yellow]{file_count / module_count:.2f}[/bold yellow]",
        f"Total Lines of Code: [bold magenta]{lines_of_code}[/bold magenta]",
        f"Total Lines of Document: [bold red]{doc_lines}[/bold red]",
    )

    # Create usage table with expanded width
    usage_table = Table(
        title="Usage Statistics",
        expand=True,
        padding=(0, 2),
        box=ROUNDED,
        title_justify="left",
    )
    usage_table.add_column(style="bold")
    usage_table.add_column("Prompt")
    usage_table.add_column("Completion")
    usage_table.add_column("Total")
    usage_table.add_row(
        "Tokens",
        str(total_prompt_tokens),
        str(total_completion_tokens),
        str(total_tokens),
    )
    usage_table.add_row(
        "Cost",
        "≈ " + format_cost(total_prompt_cost),
        "≈ " + format_cost(total_completion_cost),
        "[bold blue]" + "≈ " + format_cost(total_cost),
    )

    main_table = Table(box=None, expand=True)
    main_table.add_row(project_table)
    main_table.add_row()
    main_table.add_row(details_table)
    main_table.add_row()
    main_table.add_row(usage_table)
    main_table.add_row()

    rich_print(
        Panel(
            Align.center(main_table),
            border_style="bold green",
            title="[bold]\N{HEAVY CHECK MARK} Development Completed Successfully[/bold]",
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
                Align.center(
                    f'The output directory "{output}" already exists. Do you want to delete its contents? (Y/n)'
                ),
                border_style="bold red",
                title="Warning",
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
