from typing import Any, Set, Dict, List, Tuple, Optional


class BaseContext:
    """
    Context class for managing shared state between pipeline stages.
    Provides dictionary-like access to context information.
    """

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        """
        Initialize a new context instance.

        Args:
            initial_data: Optional dictionary with initial context data
        """
        self._data = initial_data.copy() if initial_data else {}
        self._history = []  # Track changes to context over time
        self._metadata = {}  # Store metadata about the context

    def __getitem__(self, key: str) -> Any:
        """
        Get an item from the context.

        Args:
            key: The key to retrieve

        Returns:
            The value for the given key

        Raises:
            KeyError: If the key doesn't exist in the context
        """
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set an item in the context.

        Args:
            key: The key to set
            value: The value to associate with the key
        """
        # Track the change in history
        if key in self._data:
            self._history.append(
                {
                    "operation": "update",
                    "key": key,
                    "old_value": self._data[key],
                    "new_value": value,
                }
            )
        else:
            self._history.append({"operation": "create", "key": key, "value": value})

        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        """
        Check if a key exists in the context.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get an item from the context, with a default value if it doesn't exist.

        Args:
            key: The key to retrieve
            default: Value to return if key doesn't exist

        Returns:
            The value for the given key, or the default
        """
        return self._data.get(key, default)

    def update(self, data: Dict[str, Any]) -> None:
        """
        Update the context with multiple key-value pairs.

        Args:
            data: Dictionary with values to update
        """
        for key, value in data.items():
            self[key] = value

    def copy(self) -> "BaseContext":
        """
        Create a deep copy of this context.

        Returns:
            A new instance of the same class with the same data
        """
        new_context = self.__class__(self._data)
        new_context._metadata = self._metadata.copy()
        return new_context

    def keys(self):
        """Get the keys in the context."""
        return self._data.keys()

    def values(self):
        """Get the values in the context."""
        return self._data.values()

    def items(self):
        """Get the key-value pairs in the context."""
        return self._data.items()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a plain dictionary.

        Returns:
            Dictionary with all context data
        """
        return self._data.copy()

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata about the context.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata about the context.

        Args:
            key: Metadata key
            default: Default value if key doesn't exist

        Returns:
            Metadata value or default
        """
        return self._metadata.get(key, default)

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of changes to the context.

        Returns:
            List of history entries (dictionaries)
        """
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear the history of changes."""
        self._history = []


class Context(BaseContext):
    """
    Extended context class with specific features for LLM-based multi-agent cooperation.
    Provides methods for conversation management, artifact tracking, and agent state handling.
    """

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        """Initialize the context with agent-specific structures"""
        super().__init__(initial_data)
        self._agent_data = {}  # Agent-specific data storage
        self._conversation_history = []  # Track conversation between agents
        self._artifacts = {}  # Store artifacts produced during collaboration
        self._agent_states = {}  # Track the state of each agent
        self._message_queue = []  # Queue for pending messages between agents

    def register_agent(
        self, agent_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a new agent in the context.

        Args:
            agent_id: Unique identifier for the agent
            metadata: Optional metadata about the agent (capabilities, role, etc.)
        """
        if agent_id not in self._agent_data:
            self._agent_data[agent_id] = {"metadata": metadata or {}, "memory": {}}
            self._agent_states[agent_id] = "initialized"

    def set_agent_state(self, agent_id: str, state: str) -> None:
        """
        Update the state of an agent.

        Args:
            agent_id: ID of the agent
            state: New state (e.g., 'working', 'waiting', 'completed')
        """
        if agent_id in self._agent_states:
            old_state = self._agent_states[agent_id]
            self._agent_states[agent_id] = state
            self._history.append(
                {
                    "operation": "agent_state_change",
                    "agent_id": agent_id,
                    "old_state": old_state,
                    "new_state": state,
                }
            )
        else:
            raise KeyError(f"Agent '{agent_id}' not registered")

    def get_agent_state(self, agent_id: str) -> str:
        """
        Get the current state of an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Current state of the agent
        """
        if agent_id in self._agent_states:
            return self._agent_states[agent_id]
        raise KeyError(f"Agent '{agent_id}' not registered")

    def add_agent_memory(self, agent_id: str, key: str, value: Any) -> None:
        """
        Store information in an agent's personal memory.

        Args:
            agent_id: ID of the agent
            key: Memory key
            value: Memory value
        """
        if agent_id in self._agent_data:
            self._agent_data[agent_id]["memory"][key] = value
        else:
            raise KeyError(f"Agent '{agent_id}' not registered")

    def get_agent_memory(self, agent_id: str, key: str, default: Any = None) -> Any:
        """
        Retrieve information from an agent's personal memory.

        Args:
            agent_id: ID of the agent
            key: Memory key
            default: Default value if key doesn't exist

        Returns:
            Stored memory value or default
        """
        if agent_id in self._agent_data:
            return self._agent_data[agent_id]["memory"].get(key, default)
        raise KeyError(f"Agent '{agent_id}' not registered")

    def add_message(
        self, from_agent: str, to_agent: str, content: Any, message_type: str = "text"
    ) -> int:
        """
        Add a message to the conversation history.

        Args:
            from_agent: ID of the sending agent
            to_agent: ID of the receiving agent (use 'all' for broadcasts)
            content: Message content
            message_type: Type of message (text, command, data, etc.)

        Returns:
            Message ID
        """
        message_id = len(self._conversation_history)
        timestamp = self.get_metadata("current_time", None)

        message = {
            "id": message_id,
            "from": from_agent,
            "to": to_agent,
            "content": content,
            "type": message_type,
            "timestamp": timestamp,
            "read_by": set(),
        }

        self._conversation_history.append(message)

        # If this is not a broadcast message, add to the message queue for the recipient
        if to_agent != "all":
            self._message_queue.append(message_id)

        return message_id

    def get_messages(
        self, agent_id: str, only_unread: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a specific agent.

        Args:
            agent_id: ID of the agent to get messages for
            only_unread: If True, only return unread messages

        Returns:
            List of messages
        """
        messages = []
        for msg in self._conversation_history:
            if msg["to"] == agent_id or msg["to"] == "all":
                if not only_unread or agent_id not in msg["read_by"]:
                    # Create a copy with read_by converted to a list for JSON serialization
                    msg_copy = msg.copy()
                    msg_copy["read_by"] = list(msg["read_by"])
                    messages.append(msg_copy)
        return messages

    def mark_message_read(self, agent_id: str, message_id: int) -> None:
        """
        Mark a message as read by an agent.

        Args:
            agent_id: ID of the agent marking the message
            message_id: ID of the message
        """
        if 0 <= message_id < len(self._conversation_history):
            self._conversation_history[message_id]["read_by"].add(agent_id)
        else:
            raise IndexError(f"Message ID {message_id} not found")

    def add_artifact(
        self,
        name: str,
        artifact_type: str,
        content: Any,
        creator_agent: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store an artifact produced by an agent.

        Args:
            name: Name of the artifact
            artifact_type: Type of artifact (code, image, text, etc.)
            content: The artifact content
            creator_agent: ID of the agent that created the artifact
            metadata: Optional metadata about the artifact

        Returns:
            Artifact ID
        """
        artifact_id = f"{artifact_type}_{len(self._artifacts)}"

        self._artifacts[artifact_id] = {
            "id": artifact_id,
            "name": name,
            "type": artifact_type,
            "content": content,
            "creator": creator_agent,
            "metadata": metadata or {},
            "created_at": self.get_metadata("current_time", None),
            "version": 1,
            "feedback": [],
        }

        return artifact_id

    def update_artifact(
        self, artifact_id: str, content: Any, updater_agent: str
    ) -> None:
        """
        Update an existing artifact.

        Args:
            artifact_id: ID of the artifact to update
            content: New artifact content
            updater_agent: ID of the agent updating the artifact
        """
        if artifact_id in self._artifacts:
            artifact = self._artifacts[artifact_id]
            artifact["previous_content"] = artifact["content"]
            artifact["content"] = content
            artifact["last_updated_by"] = updater_agent
            artifact["last_updated_at"] = self.get_metadata("current_time", None)
            artifact["version"] += 1
        else:
            raise KeyError(f"Artifact '{artifact_id}' not found")

    def add_artifact_feedback(
        self, artifact_id: str, feedback: str, agent_id: str
    ) -> None:
        """
        Add feedback to an artifact.

        Args:
            artifact_id: ID of the artifact
            feedback: Feedback content
            agent_id: ID of the agent providing feedback
        """
        if artifact_id in self._artifacts:
            self._artifacts[artifact_id]["feedback"].append(
                {
                    "agent": agent_id,
                    "content": feedback,
                    "timestamp": self.get_metadata("current_time", None),
                }
            )
        else:
            raise KeyError(f"Artifact '{artifact_id}' not found")

    def get_artifact(self, artifact_id: str) -> Dict[str, Any]:
        """
        Get an artifact by ID.

        Args:
            artifact_id: ID of the artifact

        Returns:
            Artifact data
        """
        if artifact_id in self._artifacts:
            return self._artifacts[artifact_id]
        raise KeyError(f"Artifact '{artifact_id}' not found")

    def get_artifacts_by_type(self, artifact_type: str) -> List[Dict[str, Any]]:
        """
        Get all artifacts of a specific type.

        Args:
            artifact_type: Type of artifacts to return

        Returns:
            List of artifacts
        """
        return [a for a in self._artifacts.values() if a["type"] == artifact_type]

    def get_active_agents(self) -> Set[str]:
        """
        Get the IDs of all registered agents.

        Returns:
            Set of agent IDs
        """
        return set(self._agent_data.keys())

    def set_workflow_stage(
        self, stage: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Set the current workflow stage for the multi-agent system.

        Args:
            stage: Name of the workflow stage
            data: Optional data associated with this stage
        """
        old_stage = self.get_metadata("workflow_stage", None)
        self.set_metadata("workflow_stage", stage)
        self.set_metadata("workflow_stage_data", data or {})
        self._history.append(
            {
                "operation": "workflow_stage_change",
                "old_stage": old_stage,
                "new_stage": stage,
            }
        )

    def get_workflow_stage(self) -> Tuple[str, Dict[str, Any]]:
        """
        Get the current workflow stage information.

        Returns:
            Tuple of (stage_name, stage_data)
        """
        stage = self.get_metadata("workflow_stage", "not_started")
        data = self.get_metadata("workflow_stage_data", {})
        return stage, data

    def summarize_conversation(self, max_messages: int = None) -> str:
        """
        Generate a textual summary of the conversation history.

        Args:
            max_messages: Maximum number of messages to include (from most recent)

        Returns:
            Formatted conversation summary
        """
        messages = self._conversation_history
        if max_messages is not None:
            messages = messages[-max_messages:]

        summary = []
        for msg in messages:
            sender = msg["from"]
            receiver = msg["to"]
            content = msg["content"]
            msg_type = msg["type"]

            if receiver == "all":
                header = f"{sender} → ALL"
            else:
                header = f"{sender} → {receiver}"

            summary.append(f"[{header}] ({msg_type}): {content}")

        return "\n".join(summary)

    def checkpoint(self, name: str) -> None:
        """
        Create a named checkpoint of the current context state.

        Args:
            name: Name of the checkpoint
        """
        checkpoints = self.get_metadata("checkpoints", {})
        checkpoints[name] = {
            "data": self._data.copy(),
            "agent_data": self._agent_data.copy(),
            "agent_states": self._agent_states.copy(),
            "conversation_history_length": len(self._conversation_history),
            "artifacts": {k: v.copy() for k, v in self._artifacts.items()},
            "timestamp": self.get_metadata("current_time", None),
        }
        self.set_metadata("checkpoints", checkpoints)

    def restore_checkpoint(self, name: str) -> bool:
        """
        Restore the context to a named checkpoint.

        Args:
            name: Name of the checkpoint

        Returns:
            True if restoration was successful, False otherwise
        """
        checkpoints = self.get_metadata("checkpoints", {})
        if name not in checkpoints:
            return False

        checkpoint = checkpoints[name]
        self._data = checkpoint["data"].copy()
        self._agent_data = checkpoint["agent_data"].copy()
        self._agent_states = checkpoint["agent_states"].copy()
        # Truncate conversation history to the checkpoint length
        self._conversation_history = self._conversation_history[
            : checkpoint["conversation_history_length"]
        ]
        self._artifacts = {k: v.copy() for k, v in checkpoint["artifacts"].items()}

        # Record the restoration in history
        self._history.append(
            {
                "operation": "checkpoint_restore",
                "checkpoint_name": name,
                "timestamp": self.get_metadata("current_time", None),
            }
        )

        return True
