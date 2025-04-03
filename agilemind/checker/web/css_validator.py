"""Validates CSS files."""

import tinycss2


def is_valid_css(content: str) -> bool:
    """
    Validates whether the content of a file at the given path is valid CSS.

    Args:
        content (str): Content of the file to validate.

    Returns:
        bool: True if the file contains valid CSS, False otherwise.
    """
    try:
        # Parse the CSS content
        stylesheet = tinycss2.parse_stylesheet(content)

        # Check for parse errors
        for node in stylesheet:
            if node.type == "error":
                return False

        return True
    except Exception:
        # Any exception during reading or parsing indicates invalid CSS
        return False
