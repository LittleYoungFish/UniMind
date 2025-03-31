from .definition import Task, TaskAgent
from agilemind.prompt import fixed_prompt
from agilemind.execution import GenerationParams

demand_analysis = Task(
    name="demand_analysis",
    agent=TaskAgent(
        background=fixed_prompt.DEMAND_ANALYST_PROMPT,
        use_tool=False,
        config=GenerationParams(temperature=0.6),
    ),
    save_artifact=True,
    artifact_path="docs/demand_analysis.md",
)

architectural_design = Task(
    name="architectural_design",
    agent=TaskAgent(
        background=fixed_prompt.ARCHITECT_PROMPT,
        use_tool=False,
        config=GenerationParams(temperature=0.5),
    ),
    save_artifact=True,
    artifact_path="docs/architectural_design.md",
)
