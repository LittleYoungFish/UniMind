"""
Utility functions for loading configuration files and substituting environment variables.
"""

import os
import re
import yaml
from typing import Dict, Any
from dotenv import load_dotenv


def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load a YAML configuration file and substitute environment variables.

    Args:
        path (str): Path to the YAML config file. Defaults to "config.yaml" at project root.

    Returns:
        dict: The loaded configuration with environment variables substituted.
    """
    load_dotenv()

    if not os.path.isabs(path):
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        path = os.path.join(project_root, path)

    # Load the YAML file
    with open(path, "r") as file:
        config = yaml.safe_load(file)

    # Substitute environment variables
    config = _substitute_env_vars(config)

    return config


def _substitute_env_vars(obj: Any) -> Any:
    """
    Recursively substitute environment variables in strings within an object.

    Args:
        obj: The object to process (can be a dict, list, or scalar value)

    Returns:
        The processed object with environment variables substituted
    """
    if isinstance(obj, dict):
        return {k: _substitute_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_substitute_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        # Pattern matches ${VAR_NAME}
        pattern = r"\$\{([^}]+)\}"

        def replace_env_var(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))

        return re.sub(pattern, replace_env_var, obj)
    else:
        return obj
