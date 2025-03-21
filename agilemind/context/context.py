"""
Context module for managing state and data flow throughout the pipeline execution.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class ContextCode:
    """
    Context class that manages the code structure in the context.
    """

    structure: Dict[str, str] = {}
    uptodated: Dict[str, str] = {}

    def dump(self) -> Dict[str, str]:
        """
        Dump the code structure into a dictionary.

        Returns:
            Dictionary containing the code structure
        """
        return {"structure": self.structure, "uptodated": self.uptodated}


class Context:
    """
    Context class that manages the state and data flow throughout pipeline execution.
    """

    root_dir: str
    raw_demand: str
    document: Dict[str, str] = {}
    code: ContextCode = ContextCode()
    history: List[Dict[str, Any]] = []
    time: float = 0.0

    def __init__(self, raw_demand: str, root_dir: Optional[str] = None):
        """
        Initialize the context with the root directory and raw demand.

        Args:
            raw_demand: User demand for the software
            root_dir: Root directory path to save the software
        """
        self.root_dir = root_dir
        self.raw_demand = raw_demand
        self.time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def is_root_dir_set(self) -> bool:
        """Check if the root directory is set in the context."""
        return self.root_dir is not None

    def set_document(self, key: str, value: str) -> None:
        """
        Set a document in the context.

        Args:
            key: Key to identify the document
            value: Document content

        Returns:
            None
        """
        self.document[key] = value

    def get_document(self, key: str) -> str:
        """
        Get a document from the context.

        Args:
            key: Key to identify the document

        Returns:
            Document content
        """
        return self.document[key]

    def add_history(self, step: str, data: Dict[str, Any]) -> None:
        """
        Add a step to the history in the context.

        Args:
            step: Step name
            data: Data associated with the step

        Returns:
            None
        """
        self.history.append(
            {
                "step": step,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": data,
            }
        )

    def dump(self) -> Dict[str, Any]:
        """
        Dump the context data into a dictionary.

        Returns:
            Dictionary containing the context data
        """
        return {
            "time": self.time,
            "root_dir": self.root_dir,
            "raw_demand": self.raw_demand,
            "document": self.document,
            "code": self.code.dump(),
            "history": self.history,
        }
