import os
import shutil
import inspect
import subprocess
from tool import tool
from typing import Any, Dict, List, Optional


class Tools:
    @staticmethod
    @tool(
        "create_file",
        description="Create a file with the specified content",
    )
    def create_file(path: str, content: str) -> Dict[str, Any]:
        """
        Create a file with the specified content.
        If parent directories do not exist, they will be created.

        Args:
            path: The path to the file to create. **MUST use relative path.**
            content: The content to write to the file. When creating a code file, 'content' will be written derectly to the file so make sure it is a valid code.

        Returns:
            Dict containing success status and message
        """
        # If file already exists, return an error
        if os.path.isfile(path):
            return {"success": False, "message": f"File already exists: {path}"}

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

            with open(path, "w") as f:
                f.write(content)
            return {"success": True, "message": f"File created at {path}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to create file: {str(e)}"}

    @staticmethod
    @tool("read_file", description="Read the content of a file")
    def read_file(path: str) -> Dict[str, Any]:
        """
        Read and return the content of a file.

        Args:
            path: The path to the file to read. **MUST use relative path.**

        Returns:
            Dict containing success status, message, and file content
        """
        try:
            if not os.path.exists(path):
                return {"success": False, "message": f"File not found: {path}"}

            # Use the correct encoding for reading Chinese characters
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "success": True,
                "message": f"File read successfully",
                "content": content,
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to read file: {str(e)}"}

    @staticmethod
    @tool(
        "execute_command",
        description="Execute a shell command",
        confirmation_required=True,
    )
    def execute_command(command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a shell command. Related path **MUST be relative path.**

        Args:
            command: The command to execute
            cwd: Current working directory (optional)

        Returns:
            Dict containing success status, message, stdout and stderr
        """
        try:
            result = subprocess.run(
                command, shell=True, cwd=cwd, capture_output=True, text=True
            )

            return {
                "success": result.returncode == 0,
                "message": f"Command executed with return code {result.returncode}",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to execute command: {str(e)}"}

    @staticmethod
    @tool("list_directory", description="List contents of a directory")
    def list_directory(path: str = ".") -> Dict[str, Any]:
        """
        List contents of a directory.

        Args:
            path: The path to list (defaults to current directory). **MUST use relative path.**

        Returns:
            Dict containing success status, message, and items in the directory
        """
        try:
            items = os.listdir(path)
            file_info = []

            for item in items:
                item_path = os.path.join(path, item)
                item_type = "directory" if os.path.isdir(item_path) else "file"
                file_info.append({"name": item, "type": item_type})

            return {
                "success": True,
                "message": f"Listed directory contents of {path}",
                "items": file_info,
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to list directory: {str(e)}"}

    @staticmethod
    @tool(
        "delete_file",
        description="Delete a file or directory",
        confirmation_required=True,
    )
    def delete_file(path: str) -> Dict[str, Any]:
        """
        Delete a file or directory.

        Args:
            path: The path to delete. **MUST use relative path.**

        Returns:
            Dict containing success status and message
        """
        try:
            if not os.path.exists(path):
                return {"success": False, "message": f"Path not found: {path}"}

            if os.path.isdir(path):
                shutil.rmtree(path)
                return {"success": True, "message": f"Directory deleted: {path}"}
            else:
                os.remove(path)
                return {"success": True, "message": f"File deleted: {path}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to delete: {str(e)}"}


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
            # Check if all required arguments are provided
            missing_args = []
            sig = inspect.signature(method)
            for param_name, param in sig.parameters.items():
                # Required params have no default and aren't variadic (*args, **kwargs)
                if param.default is param.empty and param.kind not in (
                    param.VAR_POSITIONAL,
                    param.VAR_KEYWORD,
                ):
                    if param_name not in arguments:
                        missing_args.append(param_name)
            if missing_args:
                return {
                    "success": False,
                    "message": f"Missing required arguments: {', '.join(missing_args)}",
                }

            # Check if confirmation is required
            if (
                hasattr(method, "confirmation_required")
                and method.confirmation_required
            ):
                # Format arguments as a readable string
                args_str = "\n".join(f"{k}={repr(v)}" for k, v in arguments.items())

                # Ask for confirmation
                confirmation = input(
                    f"Do you want to execute {tool_name}? (y/n)\n{args_str}"
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
