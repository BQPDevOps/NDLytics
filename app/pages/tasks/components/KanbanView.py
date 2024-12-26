from __future__ import annotations
from typing import Callable, Optional, Protocol
from nicegui import ui
from modules import StyleManager
from middleware.dynamo import DynamoMiddleware
from middleware.cognito import CognitoMiddleware
from config import config
from utils.func.util_functions import truncate_text, get_ordinal_suffix
from datetime import datetime


def format_priority(priority: int) -> str:
    priority_map = {1: "Low", 2: "Medium", 3: "High"}
    return priority_map.get(priority, "Unknown")


def format_date(date_str: str) -> str:
    try:
        if isinstance(date_str, datetime):
            date_obj = date_str
        else:
            date_obj = datetime.strptime(date_str.split(".")[0], "%Y-%m-%d %H:%M:%S")

        day = date_obj.day
        suffix = get_ordinal_suffix(day)
        return date_obj.strftime(f"%A, %B {day}{suffix}")
    except (ValueError, AttributeError):
        return date_str


class Task(Protocol):
    task_name: str


dragged: Optional[TaskCard] = None


class KanbanColumn(ui.column):
    def __init__(
        self, name: str, on_drop: Optional[Callable[[Task, str], None]] = None
    ) -> None:
        super().__init__()
        with self.classes("bg-blue-100 w-80 h-full p-4 rounded-lg shadow-lg"):
            ui.label(name).classes("text-lg font-bold text-gray-700 mb-4")
        self.name = name
        self.on("dragover.prevent", self.highlight)
        self.on("dragleave", self.unhighlight)
        self.on("drop", self.move_card)
        self.on_drop = on_drop

    def highlight(self) -> None:
        self.classes(remove="bg-blue-100", add="bg-blue-200")

    def unhighlight(self) -> None:
        self.classes(remove="bg-blue-200", add="bg-blue-100")

    def move_card(self) -> None:
        global dragged
        self.unhighlight()
        dragged.parent_slot.parent.remove(dragged)
        with self:
            TaskCard(dragged.task)
        if self.on_drop:
            self.on_drop(dragged.task, self.name.lower())
        dragged = None


class TaskCard(ui.card):
    def __init__(self, task: dict) -> None:
        super().__init__()
        self.task = task
        with self.props("draggable").classes(
            "w-full mb-4 cursor-move bg-white hover:bg-gray-50"
        ):
            with ui.column().classes("p-4 gap-2"):
                ui.label(task["task_name"]).classes("font-bold text-gray-800")
                ui.label(truncate_text(task["task_description"], 100)).classes(
                    "text-sm text-gray-600"
                )
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label(format_date(task["task_due_date"])).classes(
                        "text-xs text-gray-500"
                    )
                    priority_color = {
                        1: "text-green-600",
                        2: "text-yellow-600",
                        3: "text-red-600",
                    }.get(int(task["task_priority"]), "text-gray-600")
                    ui.label(format_priority(int(task["task_priority"]))).classes(
                        f"text-xs {priority_color}"
                    )
        self.on("dragstart", self.handle_dragstart)

    def handle_dragstart(self) -> None:
        global dragged
        dragged = self


class KanbanViewComponent:
    def __init__(self, state, on_task_updated=None):
        self.state = state
        self.on_task_updated = on_task_updated
        self.style_manager = StyleManager()
        self.dynamo_middleware = DynamoMiddleware(config.aws_tasks_table_name)
        self.cognito_middleware = CognitoMiddleware()
        self._config()

    def _config(self):
        self.style_manager.set_styles(
            {
                "kanban_view": {
                    "card": """
                    width: 100%;
                    height: calc(100vh - 200px);
                    padding: 1rem;
                    background-color: #f8fafc;
                    """,
                    "container": """
                    display: flex;
                    flex-direction: row;
                    gap: 1.5rem;
                    height: 100%;
                    padding: 1rem;
                    """,
                }
            }
        )

    def _handle_task_drop(self, task: dict, status: str) -> None:
        try:
            user_id = self.cognito_middleware.get_user_id()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

            # Format status to match DynamoDB format (capitalize first letter of each word)
            formatted_status = " ".join(word.capitalize() for word in status.split())

            key = {
                "task_id": {"S": task["task_id"]},
                "user_id": {"S": task["user_id"]},
            }

            update_expr = """SET
                task_status = :status,
                task_updated_on = :updated_on,
                task_updated_by = :updated_by"""

            expr_values = {
                ":status": {"S": formatted_status},
                ":updated_on": {"S": current_time},
                ":updated_by": {"S": user_id},
            }

            self.dynamo_middleware.update_item(key, update_expr, expr_values)
            ui.notify(f"Task moved to {formatted_status}", type="positive")

            if self.on_task_updated:
                self.on_task_updated()

        except Exception as e:
            print(f"Error updating task status: {str(e)}")
            ui.notify("Error updating task status", type="negative")

    def render(self):
        tasks = self.state["tasks"].get("Items", [])

        with ui.card().style(self.style_manager.get_style("kanban_view.card")):
            with ui.row().style(self.style_manager.get_style("kanban_view.container")):
                with KanbanColumn("Pending", on_drop=self._handle_task_drop):
                    for task in tasks:
                        if (
                            task.get("task_status", {}).get("S", "").lower()
                            == "pending"
                        ):
                            formatted_task = {
                                "task_name": task.get("task_name", {}).get("S", ""),
                                "task_description": task.get(
                                    "task_description", {}
                                ).get("S", ""),
                                "task_due_date": task.get("task_due_date", {}).get(
                                    "S", ""
                                ),
                                "task_status": task.get("task_status", {}).get("S", ""),
                                "task_priority": task.get("task_priority", {}).get(
                                    "N", "1"
                                ),
                                "task_id": task.get("task_id", {}).get("S", ""),
                                "user_id": task.get("user_id", {}).get("S", ""),
                            }
                            TaskCard(formatted_task)

                with KanbanColumn("In Progress", on_drop=self._handle_task_drop):
                    for task in tasks:
                        if (
                            task.get("task_status", {}).get("S", "").lower()
                            == "in progress"
                        ):
                            formatted_task = {
                                "task_name": task.get("task_name", {}).get("S", ""),
                                "task_description": task.get(
                                    "task_description", {}
                                ).get("S", ""),
                                "task_due_date": task.get("task_due_date", {}).get(
                                    "S", ""
                                ),
                                "task_status": task.get("task_status", {}).get("S", ""),
                                "task_priority": task.get("task_priority", {}).get(
                                    "N", "1"
                                ),
                                "task_id": task.get("task_id", {}).get("S", ""),
                                "user_id": task.get("user_id", {}).get("S", ""),
                            }
                            TaskCard(formatted_task)

                with KanbanColumn("Completed", on_drop=self._handle_task_drop):
                    for task in tasks:
                        if (
                            task.get("task_status", {}).get("S", "").lower()
                            == "completed"
                        ):
                            formatted_task = {
                                "task_name": task.get("task_name", {}).get("S", ""),
                                "task_description": task.get(
                                    "task_description", {}
                                ).get("S", ""),
                                "task_due_date": task.get("task_due_date", {}).get(
                                    "S", ""
                                ),
                                "task_status": task.get("task_status", {}).get("S", ""),
                                "task_priority": task.get("task_priority", {}).get(
                                    "N", "1"
                                ),
                                "task_id": task.get("task_id", {}).get("S", ""),
                                "user_id": task.get("user_id", {}).get("S", ""),
                            }
                            TaskCard(formatted_task)
