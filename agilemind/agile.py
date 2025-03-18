"""
Development of software using Agile methodology.
"""

import os
import json
from pathlib import Path
from execution import Agent
from tool import get_all_tools
from prompt import agile_prompt
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
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        TimeElapsedColumn(),
    ) as progress:
        # Demand analysis step
        demand_task = progress.add_task("Analyzing user demand...", total=1)
        demand_analysis = demand_analyst.process(demand)
        progress.update(
            demand_task,
            completed=1,
            description="[bold green]✓ Demand analysis completed",
        )
        result["demand_analysis"] = demand_analysis

        # Architecture step
        arch_task = progress.add_task("Querying Architect...", total=1)
        architecture = architect.process(json.dumps(demand_analysis))
        # Convert the architecture from JSON format
        architecture = json.loads(architecture["content"])
        progress.update(
            arch_task, completed=1, description="[bold green]✓ Architecture created"
        )
        result["architecture"] = architecture

        modules = architecture["modules"]
        for i, module in enumerate(modules):
            module_name = module["name"]

            # Use single task for implementation
            impl_task = progress.add_task(
                f"Implementing module: {module_name}...", total=1
            )
            program = programmer.process(json.dumps(module))
            progress.update(
                impl_task,
                completed=1,
                description=f"[bold green]✓ Module {module_name} implemented",
            )

            with open(f"docs/{module_name}.json", "w") as f:
                f.write(json.dumps(program, indent=4))

            result[module_name] = program

        progress.print(
            f"[bold green]✓ Development completed! Check your software in {output}"
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
