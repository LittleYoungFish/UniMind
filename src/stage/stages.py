from .definition import Stage
from task import demand_analysis, architectural_design


design_stage = Stage(
    name="design",
    description="Responsible for the architectural design of the software to be developed",
    tasks=[demand_analysis, architectural_design],
)
