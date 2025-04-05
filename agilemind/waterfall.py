"""
Development of software using waterfall methodology.
"""

import os
import json
import time
import shutil
import readchar
from pathlib import Path
from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from rich.box import ROUNDED
from datetime import timedelta
from typing import Dict, Optional
from rich import print as rich_print
from agilemind.context import Context
from agilemind.tool import get_all_tools
from agilemind.prompt import waterfall_prompt
from agilemind.checker import python_checkers
from agilemind.utils import extract_json, format_cost
from agilemind.execution import Agent, deterministic_generation
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

debugger = Agent(
    "debugger",
    "debug software",
    waterfall_prompt.PROGRAMMER_DEBUGGING,
    tools=get_all_tools("file_system", "development"),
    generation_params=deterministic_generation,
)
quality_assurance = Agent(
    "quality_assurance",
    "assure software quality",
    waterfall_prompt.QUALITY_ASSURANCE,
    generation_params=deterministic_generation,
)
syntax_debugger = Agent(
    "syntax_debugger",
    "debug syntax",
    waterfall_prompt.SYNTAX_DEBUGGER,
    tools=get_all_tools("file_system", "development"),
    generation_params=deterministic_generation,
)
logic_programmer = Agent(
    "logic_programmer",
    "implement software logic",
    waterfall_prompt.PROGRAMMER_LOGIC,
    tools=get_all_tools("file_system", "development"),
    generation_params=deterministic_generation,
)
structure_programmer = Agent(
    "structure_programmer",
    "implement software structure",
    waterfall_prompt.PROGRAMMER_FRAMEWORK,
    tools=get_all_tools("file_system", "development"),
    generation_params=deterministic_generation,
)
architect = Agent(
    "architect",
    "create software architecture",
    waterfall_prompt.ARCHITECT,
    save_path="docs/software_architecture.json",
    generation_params=deterministic_generation,
)
demand_analyst = Agent(
    "demand_analyst",
    "analyze user demand",
    waterfall_prompt.DEMAND_ANALYST,
    save_path="docs/demand_analysis.md",
    generation_params=deterministic_generation,
)

all_agents = [
    syntax_debugger,
    debugger,
    quality_assurance,
    logic_programmer,
    structure_programmer,
    architect,
    demand_analyst,
]


def run_workflow(
    demand: str,
    max_iterations: int = 5,
    model: Optional[str] = None,
) -> dict:
    """
    Run the LLM-Agent workflow pipelines.

    Args:
        demand: User demand for the software
        max_iterations: Maximum number of iterations for each agent
        model: Model to use for all agents

    Returns:
        Dictionary containing the software development process
    """
    # Set the model for all agents
    if model:
        for agent in all_agents:
            agent.set_model(model)

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
        context.set_document("demand_analysis", demand_analysis["output"])
        context.add_history("demand_analysis", demand_analysis)
        demand_report = extract_json(demand_analysis["output"])

        # Architecture step
        arch_task = progress.add_task("Building architecture...", total=1)
        architecture = architect.process(
            context, json.dumps(demand_analysis), max_iterations
        )
        context.add_history("architecture", architecture)
        architecture = extract_json(architecture["output"])
        progress.update(
            arch_task, completed=1, description="[bold green]Architecture created"
        )
        context.set_document("architecture", json.dumps(architecture))

        # Implement modules
        modules = architecture.get("modules", [])
        modules_task = progress.add_task("Implementing modules...", total=1)
        inplemented_modules = structure_programmer.process(
            context,
            json.dumps(demand_report) + "\n\n" + json.dumps(modules),
            max_iterations,
        )
        context.add_history("modules", inplemented_modules)
        progress.update(
            modules_task, completed=1, description="[bold green]Modules implemented"
        )

        # Implement the logic of every file in parallel
        # TODO: Implement a better way to get the files
        files = list()
        logic_task = progress.add_task("Implementing code logic...", total=len(files))
        completed_count = 0
        files_subtasks = []

        def process_code_logic(file: str) -> tuple[str, Dict]:
            """
            Process the logic of a single file.

            Args:
                file: File to process

            Returns:
                Tuple containing the file name and the implemented logic
            """
            file_logic_subtask = progress.add_task(
                f"    Implementing logic for {file}...", total=1
            )
            files_subtasks.append(file_logic_subtask)

            # Prepare the input file data in XML format
            # TODO: Implement a better way to get the file data
            file_data = ""
            xml_data = f"<path>{file}</path>\n<code>{file_data}</code>"

            logic = logic_programmer.process(context, xml_data, max_iterations)
            context.add_history(f"code_logic_{file}", logic)

            progress.update(
                file_logic_subtask,
                completed=1,
                description=f"    [bold green]Logic for {file} implemented",
            )

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

        for subtask in files_subtasks:
            progress.remove_task(subtask)

        # Check the syntax of the implemented code
        syntax_task = progress.add_task(
            "Checking code syntax...", total=len(context.code.uptodated)
        )
        completed_count = 0
        syntax_subtasks = []

        def check_syntax(file: str) -> tuple[str, dict]:
            """
            Check syntax of a single file.

            Args:
                file: File to check

            Returns:
                Tuple containing the file name and any syntax errors found
            """
            file_syntax_subtask = progress.add_task(
                f"    Checking syntax for {file}...", total=1
            )
            syntax_subtasks.append(file_syntax_subtask)

            error_info = f"in {file}: \n\n"
            static_checkers_result = python_checkers.run(file)

            if static_checkers_result:
                error_info += json.dumps(static_checkers_result)
                context.add_history(f"static_check_{file}", static_checkers_result)
                syntax_debugger.process(context, error_info, max_iterations)

            progress.update(
                file_syntax_subtask,
                completed=1,
                description=f"    [bold green]Syntax for {file} checked",
            )

            return file, static_checkers_result

        # Execute syntax checks in parallel
        with ThreadPoolExecutor() as executor:
            # TODO: Implement a better way to get the files
            future_to_file = {executor.submit(check_syntax, file): file for file in []}
            for future in as_completed(future_to_file):
                _, _ = future.result()
                completed_count += 1
                progress.update(
                    syntax_task,
                    description=(
                        ("[bold green]" if completed_count == len(files) else "")
                        + f"Syntax of {completed_count}/{len(files)} files checked"
                    ),
                    completed=completed_count,
                )

        # Clean up subtasks
        for subtask in syntax_subtasks:
            progress.remove_task(subtask)

        # Quality assurance step
        qa_round = 1
        qa_task = progress.add_task("Assuring software quality...", total=1)
        qa_report = quality_assurance.process(
            context, json.dumps(list(context.code.uptodated.keys())), max_iterations
        )
        context.add_history("quality_assurance", qa_report)
        progress.update(
            qa_task,
            completed=1,
            description=f"[bold green]Quality assurance round {qa_round} completed",
        )
        qa_report = extract_json(qa_report["output"])

        # Fix the bugs if any
        if qa_report.get("is_buggy", False):
            bugs = qa_report.get("bugs", [])
            debugger_task = progress.add_task("Debugging software...", total=len(bugs))
            debug_result = debugger.process(
                context, json.dumps(qa_report), max_iterations
            )
            progress.remove_task(debugger_task)
            context.add_history("debugger", debug_result)

    # Software information
    total_time = time.time() - start_time
    time_str = str(timedelta(seconds=int(total_time)))
    software_name = architecture["name"]
    module_count = max(len(modules), 1)
    # TODO: Implement a better way to get the files
    file_count = len([])
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


def dev(demand: str, output: str, model: str, max_iterations: int) -> dict:
    """
    Run the LLM-Agent workflow pipelines.

    Args:
        demand: User demand for the software
        output: Directory path to save the software
        model: String name of the model to use
        max_iterations: Maximum number of iterations to run

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
        result = run_workflow(demand, model=model, max_iterations=max_iterations)

        with open("logs/development_record.json", "w") as f:
            f.write(json.dumps(result, indent=4))
    finally:
        os.chdir(initial_cwd)  # Restore original working directory

    return result
