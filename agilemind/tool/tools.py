import os
import json
import shutil
import inspect
import subprocess
from tool import tool
from context import Context
from typing import Any, Dict, List, Optional


class Tools:
    @staticmethod
    @tool(
        "write_file",
        description="Write content to a file. If the file already exists, it will be overwritten. Otherwise, a new file will be created.",
        group="file_system",
    )
    def write_file(context: Context, path: str, content: str) -> Dict[str, Any]:
        """
        Write content to a file. If the file already exists, it will be overwritten. Otherwise, a new file will be created.

        Args:
            path: The path to the file to write. **MUST use relative path.**
            content: The content to write to the file. When creating a code file, 'content' will be written derectly to the file so make sure it is a valid code.

        Returns:
            Dict containing success status and message
        """
        if ".." in path or path.startswith("/"):
            return {
                "success": False,
                "message": "Cannot write files outside the current directory",
            }

        overwritten = True if os.path.isfile(path) else False

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

            with open(path, "w") as f:
                f.write(content)
            return {
                "success": True,
                "message": (
                    f"File created at {path}"
                    if not overwritten
                    else f"File overwritten at {path}"
                ),
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to create file: {str(e)}"}

    @staticmethod
    @tool("read_file", description="Read the content of a file", group="file_system")
    def read_file(context: Context, path: str) -> Dict[str, Any]:
        """
        Read and return the content of a file.

        Args:
            path: The path to the file to read. **MUST use relative path.**

        Returns:
            Dict containing success status, message, and file content
        """
        if ".." in path or path.startswith("/"):
            return {
                "success": False,
                "message": "Cannot read files outside the current directory",
            }

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
        group="system",
    )
    def execute_command(
        context: Context, command: str, cwd: Optional[str] = None
    ) -> Dict[str, Any]:
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
    @tool(
        "list_directory",
        description="List contents of a directory recursively, equivalent to 'ls -R <path>'",
        group="file_system",
    )
    def list_directory(context: Context, path: str = ".") -> Dict[str, Any]:
        """
        List all items in a directory recursively.

        Args:
            path: The path to list contents recursively (defaults to current working directory). **MUST use relative path.**

        Returns:
            Dict containing success status, message, and items in the directory
        """
        if ".." in path or path.startswith("/"):
            return {
                "success": False,
                "message": "Cannot list files outside the current directory",
            }

        try:
            if not os.path.exists(path):
                return {"success": False, "message": f"Path not found: {path}"}

            items = []
            for root, dirs, files in os.walk(path):
                items.append(
                    {"directory": root, "files": files, "subdirectories": dirs}
                )

            return {
                "success": True,
                "message": f"Directory listed: {path}",
                "items": items,
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to list directory: {str(e)}"}

    @staticmethod
    @tool(
        "delete_file",
        description="Delete a file or directory",
        group="file_system",
    )
    def delete_file(context: Context, path: str) -> Dict[str, Any]:
        """
        Delete a file or directory.

        Args:
            path: The path of file to delete. **MUST use relative path.**

        Returns:
            Dict containing success status and message
        """
        if ".." in path or path.startswith("/"):
            return {
                "success": False,
                "message": "Cannot delete files outside the current directory",
            }

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

    @staticmethod
    @tool(
        "add_to_requirements",
        description="Add a package to the requirements file",
        group="development",
    )
    def add_to_requirements(
        context: Context, language: str, package_name: str, version: str = None
    ) -> Dict[str, Any]:
        """
        Add a package to the requirements file based on the language

        Args:
            language: The language for which to add the package
            package_name: The name of the package to add
            version: The version of the package to add (optional)

        Returns:
            Dict containing success status and message
        """
        if language.lower() == "python":
            with open("requirements.txt", "a") as f:
                if version:
                    f.write(f"{package_name}=={version}\n")
                else:
                    f.write(f"{package_name}\n")
            return {
                "success": True,
                "message": f"Added {package_name} to requirements.txt",
            }
        elif language.lower() == "javascript":
            if not os.path.exists("package.json"):
                with open("package.json", "w") as f:
                    data = {"dependencies": {}}
                    json.dump(data, f, indent=2)
            else:
                with open("package.json", "r") as f:
                    data = json.load(f)
            if "dependencies" not in data:
                data["dependencies"] = {}
            data["dependencies"][package_name] = version or "*"
            with open("package.json", "w") as f:
                json.dump(data, f, indent=2)
            return {"success": True, "message": f"Added {package_name} to package.json"}

        return {
            "success": False,
            "message": f"Unsupported language: {language}",
        }

    @staticmethod
    @tool(
        "get_code_structure",
        description="Get the code structure of a module or all modules",
        group="development",
    )
    def get_code_structure(context: Context, module: str = None) -> Dict[str, Any]:
        """
        Get the code structure of a module or all modules

        Args:
            module: The name of the module to get the structure of (optional)

        Returns:
            Dict containing success status and message
        """
        try:
            code_structure = {
                k: v
                for k, v in context.code_structure.items()
                if module is None or module in k
            }

            return {
                "success": True,
                "message": f"Code structure of {module or 'all modules'} retrieved",
                "code_structure": code_structure,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get code structure: {str(e)}",
            }


def get_all_tools(*groups) -> List[Dict[str, Any]]:
    """
    Get all tools defined with the @tool decorator in OpenAI format,
    optionally filtered by one or more groups.

    Args:
        *groups: If provided, only return tools from these groups.
                Multiple group names can be passed as separate arguments.

    Returns:
        List of tool definitions for OpenAI API
    """
    tool_schemas = []
    for name, method in inspect.getmembers(Tools):
        if hasattr(method, "is_tool") and method.is_tool:
            # If no groups specified or tool belongs to one of the specified groups
            if not groups or method.tool_group in groups:
                tool_schemas.append(method.get_openai_schema())

    return tool_schemas


def execute_tool(
    context: Context, tool_name: str, arguments: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute a tool by name with the provided arguments

    Args:
        context: The context object
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
                    if param_name not in arguments and param_name != "context":
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
            return method(context, **arguments)

    return {"success": False, "message": f"Unknown tool: {tool_name}"}
