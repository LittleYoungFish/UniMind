"""
Main entry point for the LLM-Agent workflow pipelines.
"""

import sys
import signal
import argparse
from rich.align import Align
from rich.panel import Panel
from .fixed import dev as fixed_dev
from .agile import dev as agile_dev
from rich import print as rich_print

interrupt_counter = 0


def signal_handler(sig, frame):
    """Handle SIGINT (Ctrl+C) signals"""
    global interrupt_counter
    interrupt_counter += 1

    if interrupt_counter >= 3:
        rich_print(
            Panel(
                Align.center("[bold red]Received 3 interrupts. Aborting program."),
                title="Shutting Down",
                border_style="red",
            )
        )
        sys.exit(1)
    else:
        rich_print(f"[yellow]Press Ctrl+C {3 - interrupt_counter} more times to abort")
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
        default="waterfall",
        choices=[
            "waterfall",
            "agile",
        ],
        help="Pipeline type to use for development",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="gpt-4o-mini",
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
    if method == "waterfall":
        fixed_dev(**args)
    elif method == "agile":
        agile_dev(**args)
    else:
        raise ValueError(f"Invalid pipeline method: {method}")
