"""
CLI window display using rich to show live updates.
"""

import uuid
from rich import box
from rich.live import Live
from rich.tree import Tree
from rich.table import Table
from rich.panel import Panel
from datetime import datetime
from rich.console import Console
from typing import Any, Dict, Optional, Literal


class LogWindow:
    """Live updating CLI window to display progress and logs."""

    def __init__(
        self,
        title: str = "AgileMind",
        refresh_per_second: float = 4,
        display_style: Literal["tree", "table"] = "tree",
    ):
        """
        Initialize the LogWindow.

        Args:
            title (str): The title of the window
            refresh_per_second (float): How many times per second the display refreshes
            display_style (Literal["tree", "table"]): Display style for tasks - "tree" or "table"
        """
        self.title = title
        self.console = Console()
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.task_hierarchy: Dict[str, Optional[str]] = {}  # task_id -> parent_id
        self._live: Optional[Live] = None
        self.refresh_per_second = refresh_per_second
        self.display_style = display_style

    def __enter__(self):
        """Context manager entry point."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        self.close()

    def open(self):
        """Open and display the log window."""
        self._live = Live(
            self._generate_display(),
            console=self.console,
            refresh_per_second=self.refresh_per_second,
            screen=True,
        )
        self._live.start()
        return self

    def close(self):
        """Close the log window."""
        if self._live:
            self._live.stop()
            self._live = None

    def add_task(
        self, description: str, parent_id: Optional[str] = None, status: str = "pending"
    ) -> str:
        """
        Add a new task to the window.

        Args:
            description (str): Description of the task
            parent_id (Optional[str]): Optional ID of the parent task
            status (str): Initial status of the task

        Returns:
            task_id: Identifier for the added task
        """
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            "description": description,
            "status": status,
            "time_added": datetime.now(),
        }
        self.task_hierarchy[task_id] = parent_id

        if self._live:
            self._live.update(self._generate_display())

        return task_id

    def complete_task(self, task_id: str):
        """
        Mark a task as completed.

        Args:
            task_id (str): ID of the task to complete
        """
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["time_completed"] = datetime.now()

            if self._live:
                self._live.update(self._generate_display())

    def update_task(self, task_id: str, status: str, description: Optional[str] = None):
        """
        Update a task's status and optionally its description.

        Args:
            task_id (str): ID of the task to update
            status (str): New status
            description (Optional[str]): New description (if provided)
        """
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = status
            if description:
                self.tasks[task_id]["description"] = description

            if self._live:
                self._live.update(self._generate_display())

    def set_display_style(self, style: Literal["tree", "table"]):
        """
        Set the display style for the tasks.

        Args:
            style (Literal["tree", "table"]): Either "tree" or "table"
        """
        if style not in ["tree", "table"]:
            raise ValueError("Display style must be either 'tree' or 'table'")

        self.display_style = style
        if self._live:
            self._live.update(self._generate_display())

    def _generate_display(self) -> Panel:
        """Generate the display content."""
        if self.display_style == "tree":
            main_display = self._generate_task_tree()
        else:
            main_display = self._generate_task_table()

        return Panel(
            main_display,
            title=f"[bold blue]{self.title}[/bold blue]",
            border_style="blue",
            box=box.ROUNDED,
        )

    def _generate_task_tree(self) -> Tree:
        """Generate a hierarchical tree of tasks."""
        tree = Tree("[bold]Task Hierarchy[/bold]")

        roots_found = False
        for task_id, parent in self.task_hierarchy.items():
            if parent is None:
                roots_found = True
                task = self.tasks[task_id]
                status_style = self._get_status_style(task["status"])

                # Format task info
                task_text = f"{task['description']} {status_style}"
                time_info = f"[dim](Added: {task['time_added'].strftime('%H:%M:%S')}"
                if "time_completed" in task:
                    time_info += (
                        f", Completed: {task['time_completed'].strftime('%H:%M:%S')}"
                    )
                time_info += ")[/dim]"

                branch = tree.add(f"{task_text} {time_info}")
                self._add_child_tasks(branch, task_id)

        # If no root tasks were found, create a flat tree
        if not roots_found and self.tasks:
            for task_id, task in self.tasks.items():
                status_style = self._get_status_style(task["status"])
                task_text = f"{task['description']} {status_style}"
                time_info = f"[dim](Added: {task['time_added'].strftime('%H:%M:%S')}"
                if "time_completed" in task:
                    time_info += (
                        f", Completed: {task['time_completed'].strftime('%H:%M:%S')}"
                    )
                time_info += ")[/dim]"

                tree.add(f"{task_text} {time_info}")

        return tree

    def _add_child_tasks(self, parent_branch, parent_id):
        """Add child tasks to a parent branch."""
        for task_id, parent in self.task_hierarchy.items():
            if parent == parent_id:
                task = self.tasks[task_id]
                status_style = self._get_status_style(task["status"])

                # Format task info
                task_text = f"{task['description']} {status_style}"
                time_info = f"[dim](Added: {task['time_added'].strftime('%H:%M:%S')}"
                if "time_completed" in task:
                    time_info += (
                        f", Completed: {task['time_completed'].strftime('%H:%M:%S')}"
                    )
                time_info += ")[/dim]"

                branch = parent_branch.add(f"{task_text} {time_info}")
                self._add_child_tasks(branch, task_id)

    def _generate_task_table(self) -> Table:
        """Generate a table of tasks."""
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        table.add_column("ID", style="dim", width=8)
        table.add_column("Description")
        table.add_column("Status", justify="center")
        table.add_column("Added", style="dim")
        table.add_column("Completed", style="dim")

        for i, (task_id, task) in enumerate(self.tasks.items()):
            status_style = self._get_status_style(task["status"])
            added_time = task["time_added"].strftime("%H:%M:%S")
            completed_time = (
                task.get("time_completed", "").strftime("%H:%M:%S")
                if "time_completed" in task
                else "-"
            )

            table.add_row(
                f"{i+1:2d}",
                task["description"],
                status_style,
                added_time,
                completed_time,
            )

        return table

    def _get_status_style(self, status: str) -> str:
        """Get styled status text based on status value."""
        if status == "completed":
            return "[green]COMPLETED[/green]"
        elif status == "pending":
            return "[yellow]PENDING[/yellow]"
        elif status == "failed":
            return "[red]FAILED[/red]"
        elif status == "running":
            return "[blue]RUNNING[/blue]"
        else:
            return f"[cyan]{status.upper()}[/cyan]"
