"""
Context module for managing state and data flow throughout the pipeline execution.
"""

from typing import Any, Dict, Optional


class Context:
    """
    Context class that manages the state and data flow throughout pipeline execution.
    """

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        """
        Initialize a new context.

        Args:
            initial_data: Optional initial data to populate the context
        """
        self._data = initial_data.copy() if initial_data else {}
        self._metadata = {}

    def __getitem__(self, key: str) -> Any:
        """
        Get an item from the context by key.

        Args:
            key: The key to look up

        Returns:
            The value associated with the key

        Raises:
            KeyError: If the key is not found
        """
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set an item in the context.

        Args:
            key: The key to set
            value: The value to associate with the key
        """
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get an item from the context by key, with a default value.

        Args:
            key: The key to look up
            default: The default value to return if key not found

        Returns:
            The value associated with the key, or the default
        """
        return self._data.get(key, default)

    def update(self, data: Dict[str, Any]) -> None:
        """
        Update the context with new data.

        Args:
            data: Dictionary of new data to add to the context
        """
        self._data.update(data)

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata in the context.

        Args:
            key: The metadata key
            value: The metadata value
        """
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata from the context.

        Args:
            key: The metadata key to look up
            default: The default value to return if key not found

        Returns:
            The metadata value, or the default
        """
        return self._metadata.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a dictionary.

        Returns:
            Dictionary representation of the context
        """
        return self._data.copy()

    def keys(self):
        """Return the keys in the context data."""
        return self._data.keys()

    def clear(self) -> None:
        """Clear all data from the context."""
        self._data.clear()
        self._metadata.clear()
