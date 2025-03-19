"""
Retry decorator utility for handling transient failures.
"""

import time
import logging
from functools import wraps
from typing import Type, List, Optional

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: List[Type[Exception]] = None,
    logger_name: Optional[str] = None,
):
    """
    Retry decorator for handling transient failures.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
        exceptions: List of exceptions to catch (default: all exceptions)
        logger_name: Optional logger name to use (default: module logger)

    Returns:
        A decorator function that will retry the decorated function on failure.
    """
    exceptions = exceptions or [Exception]
    log = logging.getLogger(logger_name) if logger_name else logger

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay

            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as e:
                    if attempt == max_attempts:
                        log.error(
                            f"All {max_attempts} retry attempts failed for {func.__name__}: {str(e)}"
                        )
                        raise

                    log.warning(
                        f"Attempt {attempt}/{max_attempts} for {func.__name__} failed: {str(e)}. "
                        f"Retrying in {current_delay:.2f} seconds..."
                    )

                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                    attempt += 1

        return wrapper

    return decorator
