import os
import shutil
import subprocess
from tools import tool
from typing import Any, Dict, Optional


class Tools:
    @staticmethod
    @tool(name="Create File", description="Create a file with the specified content")
    def create_file(path: str, content: str) -> Dict[str, Any]:
        """
        Create a file with the specified content.
        If parent directories do not exist, they will be created.

        Args:
            path: The path to the file to create
            content: The content to write to the file

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
    @tool(name="Read File", description="Read the content of a file")
    def read_file(path: str) -> Dict[str, Any]:
        """
        Read and return the content of a file.

        Args:
            path: The path to the file to read

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
    @tool(name="Execute Command", description="Execute a shell command")
    def execute_command(command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a shell command.

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
    @tool(name="List Directory", description="List contents of a directory")
    def list_directory(path: str = ".") -> Dict[str, Any]:
        """
        List contents of a directory.

        Args:
            path: The path to list (defaults to current directory)

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
    @tool(name="Delete File", description="Delete a file or directory")
    def delete_file(path: str) -> Dict[str, Any]:
        """
        Delete a file or directory.

        Args:
            path: The path to delete

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
