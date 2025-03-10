import inspect
from .tool_decorator import tool
from src.tool.tools import Tools
from typing import Any, Dict, List

__all__ = ["tool", "get_all_tools", "execute_tool"]


def get_all_tools() -> List[Dict[str, Any]]:
    """
    Get all tools defined with the @tool decorator in OpenAI format

    Returns:
        List of tool definitions for OpenAI API
    """
    tool_schemas = []
    for name, method in inspect.getmembers(Tools):
        if hasattr(method, "is_tool") and method.is_tool:
            tool_schemas.append(method.get_openai_schema())

    return tool_schemas


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool by name with the provided arguments

    Args:
        tool_name: Name of the tool to execute
        arguments: Arguments to pass to the tool

    Returns:
        Result of tool execution
    """
    for name, method in inspect.getmembers(Tools):
        if (
            hasattr(method, "is_tool")
            and method.is_tool
            and method.tool_name == tool_name
        ):
            # Check if confirmation is required
            if (
                hasattr(method, "confirmation_required")
                and method.confirmation_required
            ):
                # Format arguments as a readable string
                args_str = ", ".join(f"{k}={repr(v)}" for k, v in arguments.items())

                # Ask for confirmation
                confirmation = input(
                    f"Do you want to execute {tool_name}({args_str})? (y/n): "
                )

                # Check if user confirmed
                if confirmation.lower() not in ["y", "yes"]:
                    return {
                        "success": False,
                        "message": "Tool execution cancelled by user",
                    }

            # Execute the tool if confirmed or if no confirmation required
            return method(**arguments)

    return {"success": False, "message": f"Unknown tool: {tool_name}"}
