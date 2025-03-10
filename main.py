"""
Main entry point for the LLM-Agent workflow pipelines.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any
from pipeline.pipeline import Pipeline, ConditionalPipeline, PipelineStage, AgentType

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/pipeline.log")],
)

# Get logger
logger = logging.getLogger("main")


def load_pipeline_config(config_path: str) -> Dict[str, Any]:
    """
    Load pipeline configuration from a JSON file.

    Args:
        config_path: Path to the JSON configuration file

    Returns:
        Dictionary containing the pipeline configuration
    """
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load pipeline configuration: {str(e)}")
        raise


def setup_pipeline(config: Dict[str, Any]) -> Pipeline:
    """
    Create and configure a pipeline based on the provided configuration.

    Args:
        config: Pipeline configuration dictionary

    Returns:
        Configured pipeline object
    """
    # Create basic or conditional pipeline
    is_conditional = config.get("conditional", False)
    if is_conditional:
        pipeline = ConditionalPipeline(
            name=config["name"], description=config.get("description", "")
        )
    else:
        pipeline = Pipeline(
            name=config["name"], description=config.get("description", "")
        )

    # This is a simplified example - in a real application, you'd need to
    # dynamically import and instantiate the actual executor functions
    logger.info(f"Setting up pipeline: {pipeline.name}")

    # Setup stages from configuration
    if "stages" in config:
        for stage_config in config["stages"]:
            # In a real application, you would dynamically import and instantiate
            # the agent based on agent_type
            stage = PipelineStage(
                name=stage_config["name"],
                agent=DummyAgent(),  # Placeholder for actual agent instance
                agent_type=AgentType(stage_config.get("agent_type", "custom")),
                model_name=stage_config.get("model_name"),
                config=stage_config.get("config", {}),
            )

            if is_conditional and "condition" in stage_config:
                # In a real application, you would create a proper condition function
                condition = lambda ctx: True  # Placeholder condition function
                pipeline.add_conditional_stage(stage, condition)
            else:
                pipeline.add_stage(stage)

    return pipeline


class DummyAgent:
    """Dummy agent class for demonstration purposes."""

    def run(self, context, **kwargs):
        """Dummy run method."""
        return {"dummy_output": "This is a dummy result"}


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="Run LLM-Agent workflow pipelines")

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        required=True,
        help="Path to pipeline configuration JSON file",
    )

    parser.add_argument(
        "--input", "-i", type=str, help="Path to initial context JSON file (optional)"
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Path to save output context JSON file (optional)",
    )

    parser.add_argument(
        "--stage", "-s", type=str, help="Run until specific stage name (inclusive)"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--add-agent",
        "-a",
        type=str,
        default=None,
        help="Add agent type specified in the AgentType enum",
    )

    return parser.parse_args()


def main() -> None:
    """
    Main entry point for the CLI.
    """
    args = parse_args()

    # Configure logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    config = load_pipeline_config(args.config)

    # Handle the AgentType if needed
    if args.add_agent:
        logger.info(f"Adding agent type: {args.add_agent}")
        # This would be handled in a real implementation
        # For now, just log that it was requested

    # Load initial context if specified
    initial_context = None
    if args.input:
        try:
            with open(args.input, "r") as f:
                initial_context = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load initial context: {str(e)}")
            sys.exit(1)

    # Setup pipeline
    try:
        pipeline = setup_pipeline(config)
    except Exception as e:
        logger.error(f"Failed to setup pipeline: {str(e)}")
        sys.exit(1)

    # Run pipeline
    try:
        if args.stage:
            logger.info(f"Running pipeline until stage: {args.stage}")
            result_context = pipeline.run_until(args.stage, initial_context)
        else:
            logger.info(f"Running pipeline: {pipeline.name}")
            result_context = pipeline.run(initial_context)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        sys.exit(1)

    # Convert Context to dict for output
    result = result_context.to_dict()

    # Save output if requested
    if args.output:
        try:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            logger.info(f"Output saved to: {args.output}")
        except Exception as e:
            logger.error(f"Failed to save output: {str(e)}")
            sys.exit(1)
    else:
        # Print result to stdout
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
