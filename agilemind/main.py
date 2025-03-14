"""
Main entry point for the LLM-Agent workflow pipelines.
"""

import argparse
from .waterfall import dev


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="Run LLM-Agent workflow pipelines")

    parser.add_argument(
        "demand",
        type=str,
        help="Demand of the software to be developed",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Directory path to save the software",
    )
    parser.add_argument(
        "-p",
        "--pipeline",
        type=str,
        default="waterfall",
        choices=[
            "waterfall",
            # "agile",
        ],
        help="Pipeline type to use for development",
    )

    return parser.parse_args()


def entry() -> None:
    """
    Main entry point for the CLI.
    """
    args = parse_args()
    args = vars(args)
    if args["pipeline"] == "waterfall":
        args.pop("pipeline")
        dev(**args)
