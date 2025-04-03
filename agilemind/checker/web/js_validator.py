"""Validate JavaScript files."""

import esprima


def is_valid_javascript(content: str) -> bool:
    """
    Validates whether the content of a file at the given path is valid JavaScript.

    Args:
        content (str): Content of the file to validate

    Returns:
        bool: True if the content is valid JavaScript, False otherwise
    """
    return is_valid_javascript_esprima(content)


def is_valid_javascript_esprima(content: str) -> bool:
    """
    Validates whether the content of a file at the given path is valid JavaScript
    using the esprima parser if available.

    Args:
        content (str): Content of the file to validate

    Returns:
        bool: True if the content is valid JavaScript, False otherwise
    """
    try:
        # Parse the content, raise an exception if it's invalid
        esprima.parseScript(content)
        return True
    except Exception as e:
        print(f"JavaScript validation error: {e}")
        return False
