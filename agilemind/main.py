"""
Main entry point for the LLM-Agent workflow pipelines.
"""

import sys
import time
import signal
import argparse
from rich.console import Console
from .fixed import dev as fixed_dev
from .agile import dev as agile_dev
from .waterfall import dev as waterfall_dev

console = Console()
interrupt_counter = 0


def signal_handler(sig, frame):
    """Handle SIGINT (Ctrl+C) signals"""
    global interrupt_counter
    interrupt_counter += 1

    if interrupt_counter >= 3:
        print("Critical: Received 3 interrupts. Aborting.")
        time.sleep(1.5)
        console.clear()
        sys.exit(1)
    else:
        print(f"Warning: Press Ctrl+C {3 - interrupt_counter} more times to abort.")
        return


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
        default="agile",
        choices=[
            "fixed",
            "waterfall",
            "agile",
        ],
        help="Pipeline type to use for development",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        required=False,
        help="String name of the model to use",
    )
    parser.add_argument(
        "--max_iterations",
        type=int,
        default=10,
        help="Maximum number of iterations to run",
    )

    return parser.parse_args()


def entry() -> None:
    """
    Main entry point for the CLI.
    """
    # Set up the signal handler
    signal.signal(signal.SIGINT, signal_handler)

    args = parse_args()
    args = vars(args)
    method = args["pipeline"]
    args.pop("pipeline")
    if method == "fixed":
        fixed_dev(**args)
    elif method == "waterfall":
        waterfall_dev(**args)
    elif method == "agile":
        agile_dev(**args)
    else:
        raise ValueError(f"Invalid pipeline method: {method}")
