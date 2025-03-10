import inspect
from .tool_decorator import tool
from src.tools.tools import Tools
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
            return method(**arguments)

    return {"success": False, "message": f"Unknown tool: {tool_name}"}
