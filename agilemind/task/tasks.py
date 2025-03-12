from execution import GenerationParams
from .definition import Task, TaskAgent
from prompt import DEMAND_ANALYST_PROMPT, ARCHITECT_PROMPT

demand_analysis = Task(
    name="demand_analysis",
    agent=TaskAgent(
        background=DEMAND_ANALYST_PROMPT,
        use_tool=False,
        config=GenerationParams(temperature=0.6),
    ),
    save_artifact=True,
    artifact_path="docs/demand_analysis.md",
)

architectural_design = Task(
    name="architectural_design",
    agent=TaskAgent(
        background=ARCHITECT_PROMPT,
        use_tool=False,
        config=GenerationParams(temperature=0.5),
    ),
    save_artifact=True,
    artifact_path="docs/architectural_design.md",
)
