from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Task:
    """Base class representing a task that needs to be performed by an agent.

    A task encapsulates the work that needs to be done and tracks the result of its execution.
    """

    # Name of the task
    name: str
    # Description of the task, will be used as prompt for the agent
    description: str
    # Background information of the task, will be used as system message for the agent
    background: Optional[str] = None
    # Model to use for this task, if not provided, the default model will be used
    model: Optional[str] = None
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

    def __str__(self) -> str:
        """String representation of the task."""
        return f"Task({self.name}, status={self.status})"

    @classmethod
    def from_dict(cls, task_dict: Dict[str, Any]) -> "Task":
        """Create a Task instance from a dictionary."""
        return cls(**task_dict)
