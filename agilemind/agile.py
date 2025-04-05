"""
Development of software using agile methodology.
"""

import os
import json
import shutil
import readchar
import traceback
from pathlib import Path
from rich.rule import Rule
from rich.box import SIMPLE
from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from datetime import datetime
from rich.columns import Columns
from rich import print as rprint
from agilemind.tool import get_tool
from agilemind.execution import Agent
from agilemind.context import Context
from rich.console import Console, Group
from typing import Dict, List, Optional
from agilemind.prompt import agile_prompt
from concurrent.futures import ThreadPoolExecutor, as_completed
from agilemind.utils import (
    LogWindow,
    load_config,
    extract_json,
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
demand_analyst = Agent(
    name="demand_analyst",
    description="Analyze the demand of the software",
    instructions=agile_prompt.DEMAND_ANALYST,
    tools=[get_tool("write_file")],
    **extract_agent_llm_config("documentation", config),
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
supervisor = Agent(
    name="supervisor",
    description="Supervise the software development process",
    instructions=agile_prompt.DEVELOPING_SUPERVISOR,
    tools=[get_tool("work_done")],
    handoffs=[developer],
    **extract_agent_llm_config("supervisor", config),
)
debugging_engineer = Agent(
    name="debugging_engineer",
    description="Debugging the software",
    instructions=agile_prompt.DEBUGGING,
    tools=[
        get_tool("get_code_structure"),
        get_tool("read_file"),
        get_tool("write_file"),
    ],
    **extract_agent_llm_config("debugging", config),
)
qa = Agent(
    name="quality_assurance",
    description="Quality assurance for the software",
    instructions=agile_prompt.QUALITY_ASSURANCE,
    tools=[
        get_tool("run_static_analysis"),
        get_tool("get_code_structure"),
        get_tool("read_file"),
        get_tool("work_done"),
    ],
    handoffs=[debugging_engineer],
    multi_turn=True,
    **extract_agent_llm_config("debugging", config),
)

all_agents = [
    prototype_builder,
    demand_analyst,
    architect,
    developer,
    supervisor,
    qa,
    debugging_engineer,
]


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
    proto_path = Path("docs/prototype.html").resolve().as_posix()

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
                Group(
                    Align.center(f"The prototype has been developed at {proto_path}."),
                    Align.center("Please check the prototype and provide feedback."),
                    "",
                    Align.center("Are you satisfied with these functionalities? (Y/n)"),
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


def analyze_demand(
    context: Context,
    window: LogWindow,
    demand: str,
    feedback: str,
    prototype: str,
    max_iterations: int = 5,
) -> str:
    """
    Analyze the demand of the software.

    Args:
        context (Context): Context object containing the software development process
        window (LogWindow): CLI window for displaying progress
        demand (str): User demand for the software
        feedback (str): Feedback from the client
        prototype (str): Final prototype of the software
        max_iterations (int): Maximum number of iterations to run

    Raises:
        RuntimeError: If the demand analysis fails

    Returns:
        out: demand analysis document
    """
    window.log("Analyzing demand of the software...")
    demand_task = window.add_task("Analyzing demand", status="running")

    demand_info = agile_prompt.DEMAND_ANALYSIS_TEMPLATE.format(
        raw_demand=demand, feedback=feedback, prototype=prototype
    )

    round_count = 0
    while round_count < max_iterations:
        round_count += 1
        demand_analyst.process(context, demand_info, max_iterations)
        if not os.path.isfile("docs/demand_analysis.md"):
            print("Critical: Demand analysis file not found")
            continue
        break

    if not os.path.isfile("docs/demand_analysis.md"):
        print("Critical: Demand analysis file not found")
        raise RuntimeError("Demand analysis failed")

    with open("docs/demand_analysis.md", "r") as f:
        demand_analysis = f.read()
    window.complete_task(demand_task)
    return demand_analysis


def build_architecture(
    context: Context,
    window: LogWindow,
    demand_analysis: str,
    max_iterations: int = 5,
) -> tuple[List, str]:
    """
    Build a prototype of the software.

    Args:
        context (Context): Context object containing the software development process
        window (LogWindow): CLI window for displaying progress
        demand_analysis (str): Demand analysis document
        max_iterations (int): Maximum number of iterations to run

    Raises:
        RuntimeError: If the architecture building fails

    Returns:
        out: Tuple of code file list and architecture information
    """
    round_count = 0
    while round_count < max_iterations:
        round_count += 1
        window.log("Designing architecture of the software...")

        architecture_task = window.add_task("Developing architecture", status="running")
        architect.process(context, demand_analysis, max_iterations)

        if not os.path.isfile("logs/architecture.json"):
            window.log("Architecture file not found", "CRITICAL")
            continue

        with open("logs/architecture.json", "r") as f:
            architecture_json = f.read()
        json_info: Dict = extract_json(architecture_json)

        if not json_info.get("code_file_list"):
            window.log("No code files found in the architecture", "CRITICAL")
            continue

        break

    if not os.path.isfile("logs/architecture.json"):
        window.log("Architecture file not found", "CRITICAL")
        raise RuntimeError("Failed to build architecture after maximum iterations.")

    with open("logs/architecture.json", "r") as f:
        architecture_json = f.read()
        json_info: Dict = extract_json(architecture_json)

    md_info = json_info.copy()
    code_file_list_md = create_file_tree(json_info.get("code_file_list", []))

    if not code_file_list_md:
        window.log("No code files found in the architecture", "CRITICAL")
        raise RuntimeError("Failed to build architecture.")

    md_info["code_file_list"] = code_file_list_md
    architecture_md = convert_json_to_markdown(
        "introduction",
        "code_file_list",
        "class_structure",
        "call_flow",
        "state_diagram",
        data=md_info,
        title="Software System Design",
        code_languages={
            "code_file_list": "plaintext",
            "class_structure": "mermaid",
            "call_flow": "mermaid",
            "state_diagram": "mermaid",
        },
    )
    with open("docs/architecture.md", "w") as f:
        f.write(architecture_md)

    window.complete_task(architecture_task)
    return json_info.get("code_file_list", []), architecture_json


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

    def implement_and_review(architecture: str, file_path: str, max_iterations: int):
        """
        Implement and review the code for the software.

        Args:
            architecture (str): Architecture information of the software
            file_path (str): Path to the code file to implement
            max_iterations (int): Maximum number of iterations to run

        Returns:
            None
        """
        current_file_task = window.add_task(
            f"Implementing {file_path}", parent_id=code_task, status="running"
        )
        round_count = 0
        while round_count < max_iterations:
            round_count += 1
            developer.process(
                context,
                agile_prompt.DEVELOPING_TEMPLATE.format(
                    architecture=architecture, file_path=file_path
                ),
                clear_memory=False,
            )
            if not os.path.isfile(file_path):
                print(f"Warning: {file_path} file not found. Retrying...")
                continue
            break

        round_count = 0
        while round_count < max_iterations:
            round_count += 1

            window.update_task(
                current_file_task,
                status="running",
                description=f"Reviewing {file_path}",
            )

            with open(file_path, "r") as f:
                code = f.read()
            supervisor_res = supervisor.process(
                context,
                agile_prompt.SUPERVISER_TEMPLATE.format(
                    architecture=architecture, file_path=file_path, file_content=code
                ),
            )
            if supervisor_res["reason"] in ["work_done", "completed"]:
                print(f"Code review completed successfully for file {file_path}.")
                break

            if supervisor_res["reason"] != "handoff":
                print(
                    f"Warning: unintended response from supervisor: {supervisor_res['reason']}"
                )
                break

            window.update_task(
                current_file_task,
                status="running",
                description=f"Revising {file_path} based on feedback",
            )

            instruction = supervisor_res["handoff"]["instruction"]
            developer.process(
                context,
                agile_prompt.QA_FEEDBACK_TEMPLATE.format(
                    file_path=file_path, description=instruction
                ),
                clear_memory=False,
            )

        window.complete_task(current_file_task)

    with ThreadPoolExecutor() as executor:
        code_tasks = [
            executor.submit(implement_and_review, architecture, file, max_iterations)
            for file in code_file_list
        ]
        for task in as_completed(code_tasks):
            task.result()

    window.log("Code implementation completed.")
    window.complete_task(code_task)

    return


def qa_check(
    context: Context,
    window: LogWindow,
    code_file_list: List[str],
    architecture: str,
    max_iterations: int = 5,
) -> None:
    """
    Perform quality assurance checks on the implemented code.

    Args:
        context (Context): Context object containing the software development process
        window (LogWindow): CLI window for displaying progress
        code_file_list (List[str]): List of code files to check
        architecture (str): Architecture information of the software
        max_iterations (int): Maximum number of iterations to run

    Returns:
        None
    """
    round_count = 0
    while round_count < max_iterations:
        round_count += 1
        qa_task = window.add_task(
            f"Performing quality assurance checks: round {round_count}.",
            status="running",
        )
        qa_result = qa.process(
            context,
            agile_prompt.QA_CHECKING_TEMPLATE.format(
                architecture=architecture, file_list=code_file_list
            ),
            clear_memory=False,
        )
        if qa_result["reason"] in ["work_done", "completed"]:
            print("Code review completed successfully.")
            break
        if qa_result["reason"] != "handoff":
            print(f"Warning: unintended response from QA: {qa_result['reason']}")
            break

        instruction = qa_result["handoff"]["instruction"]
        debugging_engineer.process(
            context,
            agile_prompt.DEBUGGING_TEMPLATE.format(
                architecture=architecture,
                description=instruction,
            ),
        )

        window.complete_task(qa_task)

    return


def show_error_view(window: LogWindow, error: Exception) -> None:
    """
    Display a detailed error panel when an uncaught exception occurs.

    Args:
        window: The LogWindow instance for logging
        error: The exception that was caught

    Returns:
        No Return
    """
    window.log(f"Error occurred: {str(error)}", level="CRITICAL")
    window.close()

    error_type = type(error).__name__
    error_message = str(error)
    error_traceback = traceback.format_exc().strip()

    # Create a rich panel with error details
    error_panel = Panel(
        Group(
            Align.center(f"[bold red]{error_type}[/bold red]: {error_message}"),
            Rule(style="dim"),
            Align.center(f"{error_traceback}"),
            Rule(style="dim"),
            Align.center("[red]Development process interrupted due to an error.[/red]"),
            Align.center(
                "If you believe this is a bug, "
                "please report this issue to the developers."
            ),
        ),
        border_style="bold red",
        title="[bold red]Error Occurred[/bold red]",
    )

    console.clear()
    console.print(error_panel)
    exit(1)


def show_dev_summary(context: Context, window: LogWindow) -> None:
    """
    Display a summary of the development process.

    Args:
        context: The Context instance containing the development process
        window: The LogWindow instance for logging

    Returns:
        No Return
    """
    window.log("Software development process completed.")
    window.close()

    # Calculate elapsed time
    start_time = datetime.strptime(context.time, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.now()
    elapsed_time = end_time - start_time

    # Count files created (exclude docs and logs directories)
    file_count = 0
    for root, _, files in os.walk(os.getcwd()):
        # Skip docs and logs directories
        if "logs" in root:
            continue
        file_count += len(files)

    # Get token usage stats
    token_stats = context.token_usage.to_dict().get("total", {})
    prompt_tokens = token_stats.get("prompt_tokens", 0)
    completion_tokens = token_stats.get("completion_tokens", 0)
    total_tokens = prompt_tokens + completion_tokens

    # Get cost stats
    cost_stats = context.cost.to_dict().get("total", {})
    prompt_cost = cost_stats.get("prompt_cost", 0.0)
    completion_cost = cost_stats.get("completion_cost", 0.0)
    total_cost = cost_stats.get("total_cost", 0.0)

    # Main summary table
    summary_table = Table(
        title="Development Summary",
        show_header=False,
        box=None,
        width=min(80, console.width - 15),
    )
    summary_table.add_column("Category", style="cyan", no_wrap=True)
    summary_table.add_column("Value", style="green", justify="right")

    # Add main info
    summary_table.add_row("", "")
    summary_table.add_row(
        "Project Demand",
        (
            context.raw_demand[:50] + "..."
            if len(context.raw_demand) > 50
            else context.raw_demand
        ),
    )
    summary_table.add_row("Output Directory", context.root_dir)
    summary_table.add_row("Development Start Time", context.time)
    summary_table.add_row(
        "Development Duration", f"{elapsed_time.total_seconds():.2f} seconds"
    )
    summary_table.add_row("Files Created", str(file_count))

    # Usage table
    token_table = Table(title="Usage", show_header=True, box=SIMPLE, width=35)
    token_table.add_column("Type", style="cyan")
    token_table.add_column("Token", style="green", justify="right")
    token_table.add_column("Cost/USD", style="green", justify="right")
    token_table.add_row("Prompt", f"{prompt_tokens:,}", f"${prompt_cost:.3f}")
    token_table.add_row(
        "Completion", f"{completion_tokens:,}", f"${completion_cost:.3f}"
    )
    token_table.add_row("Total", f"{total_tokens:,}", f"${total_cost:.3f}")

    # Check terminal width to decide on layout
    term_width = console.width
    horizontal_width = summary_table.width + token_table.width + 15

    # Create responsive table layout
    if term_width >= horizontal_width:
        tables_layout = Columns(
            [Align.left(summary_table), Align.right(token_table)], expand=True
        )
    else:
        tables_layout = Group(
            Align.center(summary_table), "", Align.center(token_table)
        )

    # Create the final panel with all tables
    final_panel = Panel(
        Align.center(
            Group(
                Align.center(tables_layout),
                "",
                Align.center("[dim]AgileMind[/dim]"),
            )
        ),
        border_style="bold green",
        title="[bold green]Development Completed Successfully[/bold green]",
        padding=(1, 5, 0, 5),
    )

    console.clear()
    console.print(final_panel)
    exit(0)


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

    try:
        feedback, prototype = build_prototype(context, window, demand, max_iterations)
        demand_analysis = analyze_demand(
            context, window, demand, feedback, prototype, max_iterations
        )
        file_list, architecture = build_architecture(
            context, window, demand_analysis, max_iterations
        )
        implement_code(context, window, file_list, architecture, max_iterations)
        qa_check(context, window, file_list, architecture, max_iterations)

        with open("logs/development_record.json", "w") as f:
            f.write(json.dumps(context.dump(), indent=4))
    except Exception as e:
        show_error_view(window, e)

    show_dev_summary(context, window)
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
    # If output dir is not empty
    if os.path.isdir(output) and os.listdir(output):
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

        # Remove all files and subdirectories in the output directory
        for item in Path(output).glob("*"):
            if item.is_file():
                item.unlink()
            else:
                shutil.rmtree(item)

    Path(output).mkdir(parents=True, exist_ok=True)
    Path(output, "docs").mkdir(parents=True, exist_ok=True)
    Path(output, "logs").mkdir(parents=True, exist_ok=True)

    # Change current working directory to the output directory
    initial_cwd = os.getcwd()
    os.chdir(output)

    try:
        result = run_workflow(demand, model=model, max_iterations=max_iterations)
    finally:
        os.chdir(initial_cwd)  # Restore original working directory

    return result
