from .definition import Task
from .utils import save_result_to_file
from prompt import DEMAND_ANALYST_PROMPT, ARCHITECT_PROMPT

demand_analysis = Task(
    name="demand_analysis",
    background=DEMAND_ANALYST_PROMPT,
    use_tool=False,
    agent_config={"temprature": 0.8},
    artifact_path="docs/demand_analysis.md",
    post_execution=save_result_to_file,
)

architectural_design = Task(
    name="architectural_design",
    background=ARCHITECT_PROMPT,
    use_tool=False,
    agent_config={"temprature": 0.5},
    artifact_path="docs/architectural_design.md",
    post_execution=save_result_to_file,
)
