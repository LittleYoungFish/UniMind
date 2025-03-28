import re
import json
from typing import Optional


def clean_json_string(input_string: str) -> str:
    """
    Clean a string that might contain JSON with markdown or explanatory text.

    Args:
        input_string (str): A string that contains JSON, possibly with markdown formatting or explanatory text around it.

    Returns:
        out (str): A clean JSON string ready to be parsed with json.loads()

    Examples:
        ```
        clean_json_string('json: {"key": "value"}')
        {"key": "value"}
        clean_json_string('Sure! I will... {"key": "value"}')
        {"key": "value"}
        ```
    """
    if not input_string:
        return ""

    json_pattern = r"({[\s\S]*}|\[.*\])"
    json_matches = re.findall(json_pattern, input_string)

    for match in json_matches:
        try:
            json.loads(match)
            return match
        except json.JSONDecodeError:
            continue

    # If fails, return the original string but stripped of common prefixes
    cleaned = re.sub(r"^.*?({.*)", r"\1", input_string, flags=re.DOTALL)
    cleaned = re.sub(r"(}[^}]*)$", r"}", cleaned, flags=re.DOTALL)

    try:
        json.loads(cleaned)
        return cleaned
    except json.JSONDecodeError:
        # If we can't find valid JSON, return the original string
        # as it might be malformed but the caller might want to handle it
        return input_string.strip()


def extract_json(input_string: str) -> Optional[dict]:
    """
    Extract and parse JSON from a string that might have markdown or explanatory text.

    Args:
        input_string (str): A string that contains JSON, possibly with markdown formatting or explanatory text around it.

    Returns:
        out (Optional[dict]): The parsed JSON as a dictionary, or None if parsing fails
    """
    try:
        cleaned = clean_json_string(input_string)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {}
