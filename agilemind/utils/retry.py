"""
Retry decorator utility for handling transient failures with Rich visualization.
"""

import time
from rich.box import SIMPLE
from functools import wraps
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from typing import Type, List
from rich.console import Console

console = Console()


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 3.0,
    exceptions: List[Type[Exception]] = None,
):
    """
    Retry decorator for handling transient failures with Rich visualization.
    Uses techniques that don't conflict with other Live displays.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
        exceptions: List of exceptions to catch (default: all exceptions)

    Returns:
        A decorator function that will retry the decorated function on failure.
    """
    exceptions = exceptions or [Exception]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            table = None

            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)

                except tuple(exceptions) as e:
                    # Create a simple table for retry status
                    table = Table(box=SIMPLE)
                    table.add_column("Attempt", style="cyan")
                    table.add_column("Function", style="blue")
                    table.add_column("Error", style="yellow")
                    table.add_column("Next retry", style="green")
                    table.add_row(
                        f"{attempt}/{max_attempts}",
                        func.__name__,
                        str(e),
                        f"in {current_delay:.2f}s",
                    )
                    if attempt < max_attempts:
                        console.print(
                            Panel(
                                Align.center(table),
                                title="Retry in Progress",
                                border_style="yellow",
                            ),
                            new_line_start=True,
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                        attempt += 1
                    else:
                        console.print(
                            Panel(
                                Align.center(table),
                                title="Max Retries Exceeded",
                                border_style="red bold",
                            ),
                            new_line_start=True,
                        )
                        exit(1)

        return wrapper

    return decorator
