"""
Main entry point for the LLM-Agent workflow pipelines.
"""

import argparse


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="Run LLM-Agent workflow pipelines")

    parser.add_argument(
        "demand", type=str, help="Demand of the software to be developed"
    )
    parser.add_argument(
        "-o", "--output", type=str, help="Directory path to save the software"
    )

    return parser.parse_args()


def run(demand: str, output: str) -> None:
    """
    Run the LLM-Agent workflow pipelines.

    Args:
        demand: Demand of the software to be developed
        output: Directory path to save the software
    """
    pass


def main() -> None:
    """
    Main entry point for the CLI.
    """
    args = parse_args()
    run(**vars(args))
