"""
Stage module for organizing tasks within a pipeline.
"""

from task import ITask
from execution import Executor
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable


class IStage(ABC):
    """Interface for pipeline stages."""

    name: str
    description: Optional[str] = None
    tasks: List[ITask] = field(default_factory=list)

    @abstractmethod
    def add_task(self, *tasks: ITask) -> "IStage":
        """Add one or more tasks to the stage."""
        pass

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the stage and return the updated context."""
        pass


@dataclass
class Stage(IStage):
    """A stage in a pipeline, containing one or more tasks to be executed."""

    def __post_init__(self):
        """Validate stage attributes after initialization."""
        if not self.name:
            raise ValueError("Stage must have a name")
        if not self.tasks:
            self.tasks = []

    def add_task(self, *tasks: ITask) -> "Stage":
        """
        Add one or more tasks to the stage.

        Args:
            tasks: The task(s) to add

        Returns:
            Self for chaining
        """
        for task in tasks:
            self.tasks.append(task)
        return self

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute all tasks in the stage and update the context.

        Args:
            context: Current pipeline context

        Returns:
            Updated context with task results
        """

        executor: Executor = context.get("executor")
        if not executor:
            raise ValueError("No executor found in context")

        for i, task in enumerate(self.tasks):
            try:
                result = executor.execute(task)
                context[f"task_{task.get_name()}_result"] = result

                # Stop execution if task failed and we're not set to continue
                if task.get_status() == "failed" and not context.get(
                    "continue_on_failure", False
                ):
                    break

            except Exception as e:
                context[f"task_{task.get_name()}_error"] = str(e)
                if not context.get("continue_on_failure", False):
                    raise

        return context


@dataclass
class ConditionalStage(Stage):
    """A stage that only executes if a condition is met."""

    condition: Callable[[Dict[str, Any]], bool]

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the stage if the condition is met.

        Args:
            context: Current pipeline context

        Returns:
            Updated context, or unchanged if condition not met
        """
        if self.condition(context):
            return super().execute(context)
        else:
            context[f"stage_{self.name}_skipped"] = True
            return context
