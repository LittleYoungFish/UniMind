"""
LLM-Agent Workflow Pipeline
Orchestrates the flow between different LLM-based agents and workflows.
"""

import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Callable


class AgentType(Enum):
    """Enumeration of available agent types in the pipeline."""

    CUSTOM = "custom"
    # TODO Add agent type


class PipelineStage:
    """Represents a single stage in the LLM agent pipeline."""

    def __init__(
        self,
        name: str,
        agent_type: AgentType,
        executor: Callable,
        input_mapping: Optional[Dict[str, str]] = None,
        output_mapping: Optional[Dict[str, str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a pipeline stage.

        Args:
            name: Unique identifier for the stage
            agent_type: Type of agent to use for this stage
            executor: Function or callable that executes the agent's task
            input_mapping: Maps pipeline context keys to agent input parameters
            output_mapping: Maps agent output keys to pipeline context keys
            config: Additional configuration for the agent
        """
        self.name = name
        self.agent_type = agent_type
        self.executor = executor
        self.input_mapping = input_mapping or {}
        self.output_mapping = output_mapping or {}
        self.config = config or {}

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute this pipeline stage.

        Args:
            context: Current pipeline context

        Returns:
            Updated context with this stage's outputs
        """
        # Map inputs from context to agent inputs
        agent_inputs = {}
        for agent_param, context_key in self.input_mapping.items():
            if context_key in context:
                agent_inputs[agent_param] = context[context_key]

        # Apply any configuration
        for key, value in self.config.items():
            if key not in agent_inputs:
                agent_inputs[key] = value

        # Execute the agent
        agent_outputs = self.executor(**agent_inputs)

        # Map agent outputs back to context
        for agent_output, context_key in self.output_mapping.items():
            if agent_output in agent_outputs:
                context[context_key] = agent_outputs[agent_output]

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
        self.context: Dict[str, Any] = {}
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

    def run(self, initial_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run the entire pipeline from start to finish.

        Args:
            initial_context: Initial context data to start with

        Returns:
            Final context after all stages have executed
        """
        self.context = initial_context.copy() if initial_context else {}
        self.logger.info(f"Starting pipeline: {self.name}")

        for i, stage in enumerate(self.stages):
            try:
                self.logger.info(
                    f"Executing stage {i+1}/{len(self.stages)}: {stage.name}"
                )
                self.context = stage.execute(self.context)
                self.logger.info(f"Completed stage: {stage.name}")
            except Exception as e:
                self.logger.error(f"Error in stage {stage.name}: {str(e)}")
                raise

        self.logger.info(f"Pipeline {self.name} completed successfully")
        return self.context

    def run_until(
        self, stage_name: str, initial_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the pipeline until a specific stage is reached.

        Args:
            stage_name: Name of the stage to stop at (inclusive)
            initial_context: Initial context data to start with

        Returns:
            Context after executing up to and including the specified stage
        """
        self.context = initial_context.copy() if initial_context else {}

        for stage in self.stages:
            self.context = stage.execute(self.context)
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
        self.condition_map: Dict[str, Callable[[Dict[str, Any]], bool]] = {}

    def add_conditional_stage(
        self, stage: PipelineStage, condition: Callable[[Dict[str, Any]], bool]
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

    def run(self, initial_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run the pipeline, skipping stages whose conditions evaluate to False.

        Args:
            initial_context: Initial context data to start with

        Returns:
            Final context after all applicable stages have executed
        """
        self.context = initial_context.copy() if initial_context else {}
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
                self.logger.info(f"Completed stage: {stage.name}")
            except Exception as e:
                self.logger.error(f"Error in stage {stage.name}: {str(e)}")
                raise

        self.logger.info(f"Pipeline {self.name} completed successfully")
        return self.context
