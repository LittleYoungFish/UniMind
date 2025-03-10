"""
Pipeline module for orchestrating the flow of data through a series of agents.
"""

import logging
from context import Context
from execution import AgentType
from typing import Dict, List, Any, Optional, Callable


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
