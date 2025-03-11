from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional


class ITask(ABC):
    """Interface for all tasks in the system."""

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the task and return the result."""
        pass

    @abstractmethod
    def get_status(self) -> str:
        """Get the current status of the task."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of the task."""
        pass


@dataclass
class Task(ITask):
    """Base class representing a task that needs to be performed by an agent.

    A task encapsulates the work that needs to be done and tracks the result of its execution.
    """

    # Name of the task
    name: str
    # Description of the task, will be used as prompt for the agent
    description: str
    # Background information of the task, will be used as system message for the agent
    background: Optional[str] = None
    # Whether to allow to use a tool for this task
    use_tool: bool = False
    # Result of the task execution
    result: Optional[Dict[str, Any]] = None
    # Status of the task, may be: pending, in_progress, completed, failed
    status: str = "pending"
    # Configuration for the agent to use for this task
    agent_config: Optional[Dict[str, Any]] = None
    # Store additional metadata about the task
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate task attributes after initialization."""
        if not self.name:
            raise ValueError("Task must have a name")
        if not self.description:
            raise ValueError("Task must have a description")

    def set_result(self, result: Dict[str, Any]) -> None:
        """Set the result of the task execution."""
        self.result = result
        self.status = "completed"

    def set_failed(self, error: Optional[str] = None) -> None:
        """Mark the task as failed with optional error information."""
        self.status = "failed"
        self.metadata["error"] = error or "Task failed for unknown reason"

    def is_complete(self) -> bool:
        """Check if the task is completed."""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if the task has failed."""
        return self.status == "failed"

    def _enrich_description(self, context: Dict[str, Any]) -> str:
        """Enrich the task description with context information if needed."""
        return self.description  # TODO: Implement this method

    def __str__(self) -> str:
        """String representation of the task."""
        return f"Task({self.name}, status={self.status})"


@dataclass
class TaskGroup(ITask):
    """A group of tasks that can be executed together."""

    name: str
    tasks: List[ITask] = field(default_factory=list)
    status: str = "pending"

    def add_task(self, task: ITask) -> None:
        """Add a task to the group."""
        self.tasks.append(task)

    def remove_task(self, task_name: str) -> None:
        """Remove a task from the group by name."""
        self.tasks = [task for task in self.tasks if task.get_name() != task_name]

    def __str__(self) -> str:
        """String representation of the task group."""
        return f"TaskGroup({self.name}, tasks={len(self.tasks)}, status={self.status})"
