"""
CLI window display using rich to show live updates and logs.
"""

from rich.text import Text
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from collections import deque
from rich.layout import Layout
from rich.console import Group
from rich.spinner import Spinner
from typing import Optional, Deque, Dict, Any


class LogWindow:
    """Live updating CLI window to display progress and logs."""

    def __init__(self, title: str = "Agile Mind", max_logs: int = 5):
        """
        Initialize the CLI window.

        Args:
            title: Window title
            max_logs: Maximum number of log entries to display
        """
        self.title = title
        self.max_logs = max_logs
        self.logs: Deque[str] = deque(maxlen=max_logs)
        self.current_status: str = "Initializing..."
        self.current_step: str = ""
        self.live: Optional[Live] = None
        self.active_spinner: Optional[str] = None
        self.tasks: Dict[str, Dict[str, Any]] = {}

    def __enter__(self):
        """Start the live display when entering context."""
        self.live = Live(
            self._generate_layout(), auto_refresh=True, refresh_per_second=4
        )
        self.live.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the live display when exiting context."""
        if self.live:
            self.live.__exit__(exc_type, exc_val, exc_tb)

    def update_status(self, status: str):
        """Update the current status."""
        self.current_status = status
        self._refresh()

    def start_task(self, task_id: str, description: str):
        """Start a new task with a spinner."""
        self.tasks[task_id] = {
            "description": description,
            "status": "running",
            "spinner": Spinner("dots", text=description),
        }
        self.active_spinner = task_id
        self._refresh()

    def complete_task(self, task_id: str):
        """Mark a task as completed."""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "completed"
            if self.active_spinner == task_id:
                self.active_spinner = None
        self._refresh()

    def log(self, message: str):
        """Add a log message to the window."""
        self.logs.append(message)
        self._refresh()

    def _generate_layout(self) -> Panel:
        """Generate the layout for the CLI window."""
        # Create top status section
        status_text = Text(f"Status: {self.current_status}", style="bold blue")

        # Create task progress section
        tasks_table = Table(show_header=False, box=None, padding=(0, 1))
        tasks_table.add_column(width=2)
        tasks_table.add_column()

        for task_id, task in self.tasks.items():
            if task["status"] == "completed":
                tasks_table.add_row("✓", task["description"], style="green")
            elif self.active_spinner == task_id:
                tasks_table.add_row(task["spinner"], task["description"])
            else:
                tasks_table.add_row("•", task["description"], style="dim")

        # Create logs section
        log_lines = [Text(log) for log in self.logs]
        if not log_lines:
            log_lines = [Text("No logs yet...", style="dim")]

        logs_panel = Panel(
            Group(*log_lines),
            title="Logs",
            height=min(len(log_lines) + 2, self.max_logs + 2),
        )

        # Combine all sections
        layout = Layout()
        layout.split(
            Layout(status_text, name="status", size=1),
            Layout(tasks_table, name="tasks", size=len(self.tasks) + 1),
            Layout(logs_panel, name="logs", size=self.max_logs + 2),
        )

        return Panel(layout, title=self.title, border_style="blue")

    def _refresh(self):
        """Refresh the live display."""
        if self.live:
            self.live.update(self._generate_layout())
