"""
LLM-Agent Workflow Pipeline
Orchestrates the flow between different LLM-based agents and workflows.
"""

import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Callable


class Context:
    """
    Context class for managing shared state between pipeline stages and agents.
    Provides dictionary-like access to context information and additional utility methods
    for tracking pipeline execution state.
    """

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        """
        Initialize a new context instance.

        Args:
            initial_data: Optional dictionary with initial context data
        """
        self._data = initial_data.copy() if initial_data else {}
        self._history = []  # Track changes to context over time
        self._metadata = {}  # Store metadata about the context

    def __getitem__(self, key: str) -> Any:
        """
        Get an item from the context.

        Args:
            key: The key to retrieve

        Returns:
            The value for the given key

        Raises:
            KeyError: If the key doesn't exist in the context
        """
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set an item in the context.

        Args:
            key: The key to set
            value: The value to associate with the key
        """
        # Track the change in history
        if key in self._data:
            self._history.append(
                {
                    "operation": "update",
                    "key": key,
                    "old_value": self._data[key],
                    "new_value": value,
                }
            )
        else:
            self._history.append({"operation": "create", "key": key, "value": value})

        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        """
        Check if a key exists in the context.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get an item from the context, with a default value if it doesn't exist.

        Args:
            key: The key to retrieve
            default: Value to return if key doesn't exist

        Returns:
            The value for the given key, or the default
        """
        return self._data.get(key, default)

    def update(self, data: Dict[str, Any]) -> None:
        """
        Update the context with multiple key-value pairs.

        Args:
            data: Dictionary with values to update
        """
        for key, value in data.items():
            self[key] = value

    def copy(self) -> "Context":
        """
        Create a deep copy of this context.

        Returns:
            A new Context instance with the same data
        """
        new_context = Context(self._data)
        new_context._metadata = self._metadata.copy()
        return new_context

    def keys(self):
        """Get the keys in the context."""
        return self._data.keys()

    def values(self):
        """Get the values in the context."""
        return self._data.values()

    def items(self):
        """Get the key-value pairs in the context."""
        return self._data.items()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a plain dictionary.

        Returns:
            Dictionary with all context data
        """
        return self._data.copy()

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata about the context.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata about the context.

        Args:
            key: Metadata key
            default: Default value if key doesn't exist

        Returns:
            Metadata value or default
        """
        return self._metadata.get(key, default)

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of changes to the context.

        Returns:
            List of history entries (dictionaries)
        """
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear the history of changes."""
        self._history = []


class AgentType(Enum):
    """Enumeration of available agent types in the pipeline."""

    CUSTOM = "custom"
    # TODO Add agent type


class PipelineStage:
    """Represents a single stage in the LLM agent pipeline."""

    def __init__(
        self,
        name: str,
        agent: Any,
        agent_type: AgentType,
        model_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a pipeline stage.

        Args:
            name: Unique identifier for the stage
            agent: The agent instance to use for this stage
            agent_type: Type of agent to use for this stage
            model_name: Name of the model to use with this agent
            config: Additional configuration for the agent
        """
        self.name = name
        self.agent = agent
        self.agent_type = agent_type
        self.model_name = model_name
        self.config = config or {}

    def execute(self, context: Context) -> Context:
        """
        Execute this pipeline stage.

        Args:
            context: Current pipeline context

        Returns:
            Updated context with this stage's outputs
        """
        # Execute the agent with the current context and configuration
        result = self.agent.run(context=context, **self.config)
        # Update the context with the agent's results
        if isinstance(result, dict):
            context.update(result)
        else:
            context[f"{self.name}_result"] = result
        return context


class Pipeline:
    """
    Pipeline class that orchestrates the flow between different LLM-based agents.
    """

    def __init__(self, name: str, description: Optional[str] = None):
        """
        Initialize a new pipeline.

        Args:
            name: Name of the pipeline
            description: Optional description
        """
        self.name = name
        self.description = description
        self.stages: List[PipelineStage] = []
        self.context = Context()
        self.logger = logging.getLogger(f"pipeline.{name}")

    def add_stage(self, stage: PipelineStage) -> "Pipeline":
        """
        Add a stage to the pipeline.

        Args:
            stage: The pipeline stage to add

        Returns:
            Self for chaining
        """
        self.stages.append(stage)
        return self

    def add_stages(self, stages: List[PipelineStage]) -> "Pipeline":
        """
        Add multiple stages to the pipeline.

        Args:
            stages: List of pipeline stages to add

        Returns:
            Self for chaining
        """
        self.stages.extend(stages)
        return self

    def run(self, initial_context: Optional[Dict[str, Any]] = None) -> Context:
        """
        Run the entire pipeline from start to finish.

        Args:
            initial_context: Initial context data to start with

        Returns:
            Final context after all stages have executed
        """
        self.context = Context(initial_context) if initial_context else Context()
        self.logger.info(f"Starting pipeline: {self.name}")

        for i, stage in enumerate(self.stages):
            try:
                self.logger.info(
                    f"Executing stage {i+1}/{len(self.stages)}: {stage.name}"
                )
                self.context = stage.execute(self.context)
                self.context.set_metadata("last_executed_stage", stage.name)
                self.logger.info(f"Completed stage: {stage.name}")
            except Exception as e:
                self.logger.error(f"Error in stage {stage.name}: {str(e)}")
                raise

        self.logger.info(f"Pipeline {self.name} completed successfully")
        return self.context

    def run_until(
        self, stage_name: str, initial_context: Optional[Dict[str, Any]] = None
    ) -> Context:
        """
        Run the pipeline until a specific stage is reached.

        Args:
            stage_name: Name of the stage to stop at (inclusive)
            initial_context: Initial context data to start with

        Returns:
            Context after executing up to and including the specified stage
        """
        self.context = Context(initial_context) if initial_context else Context()

        for stage in self.stages:
            self.context = stage.execute(self.context)
            self.context.set_metadata("last_executed_stage", stage.name)
            if stage.name == stage_name:
                break

        return self.context


class ConditionalPipeline(Pipeline):
    """
    Extended pipeline that supports conditional execution of stages.
    """

    def __init__(self, name: str, description: Optional[str] = None):
        """Initialize a new conditional pipeline."""
        super().__init__(name, description)
        self.condition_map: Dict[str, Callable[[Context], bool]] = {}

    def add_conditional_stage(
        self, stage: PipelineStage, condition: Callable[[Context], bool]
    ) -> "ConditionalPipeline":
        """
        Add a stage that only executes if the condition function returns True.

        Args:
            stage: The pipeline stage to add
            condition: Function that takes the context and returns a boolean

        Returns:
            Self for chaining
        """
        self.stages.append(stage)
        self.condition_map[stage.name] = condition
        return self

    def run(self, initial_context: Optional[Dict[str, Any]] = None) -> Context:
        """
        Run the pipeline, skipping stages whose conditions evaluate to False.

        Args:
            initial_context: Initial context data to start with

        Returns:
            Final context after all applicable stages have executed
        """
        self.context = Context(initial_context) if initial_context else Context()
        self.logger.info(f"Starting conditional pipeline: {self.name}")

        for i, stage in enumerate(self.stages):
            # Check if this stage has a condition
            if stage.name in self.condition_map:
                condition_met = self.condition_map[stage.name](self.context)
                if not condition_met:
                    self.logger.info(
                        f"Skipping stage {i+1}/{len(self.stages)}: {stage.name} (condition not met)"
                    )
                    continue

            try:
                self.logger.info(
                    f"Executing stage {i+1}/{len(self.stages)}: {stage.name}"
                )
                self.context = stage.execute(self.context)
                self.context.set_metadata("last_executed_stage", stage.name)
                self.logger.info(f"Completed stage: {stage.name}")
            except Exception as e:
                self.logger.error(f"Error in stage {stage.name}: {str(e)}")
                raise

        self.logger.info(f"Pipeline {self.name} completed successfully")
        return self.context
