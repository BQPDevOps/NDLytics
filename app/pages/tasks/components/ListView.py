from nicegui import ui
from modules import StyleManager
from middleware.dynamo import DynamoMiddleware
from middleware.cognito import CognitoMiddleware
from config import config
from utils.func.util_functions import truncate_text, get_ordinal_suffix
from datetime import datetime
from .TaskView import TaskViewComponent


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


class ListViewComponent:
    def __init__(self, state, on_click_select_task):
        self.state = state
        self.on_click_select_task = on_click_select_task
        self.style_manager = StyleManager()
        self.dynamo_middleware = DynamoMiddleware(config.aws_tasks_table_name)
        self._config()

    def _config(self):
        self.style_manager.set_styles(
            {
                "list_view": {
                    "card": """
                    width: 100%;
                    height: calc(100vh - 200px);
                    padding: 1rem;
                    background-color: #f8fafc;
                    """
                }
            }
        )

    def _format_grid_data(self, tasks):
        return [
            {
                "title": task.get("task_name", {}).get("S", ""),
                "description": truncate_text(
                    task.get("task_description", {}).get("S", ""), 50
                ),
                "due_date": format_date(task.get("task_due_date", {}).get("S", "")),
                "status": task.get("task_status", {}).get("S", ""),
                "priority": format_priority(
                    int(task.get("task_priority", {}).get("N", "1"))
                ),
                "raw_data": {
                    "task_name": task.get("task_name", {}).get("S", ""),
                    "task_description": task.get("task_description", {}).get("S", ""),
                    "task_due_date": task.get("task_due_date", {}).get("S", ""),
                    "task_status": " ".join(
                        word.capitalize()
                        for word in task.get("task_status", {})
                        .get("S", "pending")
                        .split()
                    ),
                    "task_priority": int(task.get("task_priority", {}).get("N", "1")),
                    "task_tags": task.get("task_tags", {}).get("S", ""),
                    "task_id": task.get("task_id", {}).get("S", ""),
                    "user_id": task.get("user_id", {}).get("S", ""),
                    "task_comments": task.get("task_comments", {"L": []}),
                },
            }
            for task in tasks.get("Items", [])
        ]

    def _on_row_clicked(self, e):
        task_data = e.args["data"]["raw_data"]
        dialog = ui.dialog().props("maximized persistent")
        with dialog:
            TaskViewComponent(
                task_data=task_data,
                on_save=lambda t: self._save_task(t, dialog),
                on_cancel=dialog.close,
            ).render()
        dialog.open()

    def _save_task(self, task_data, dialog):
        try:
            self.dynamo_middleware.put_item(task_data)
            ui.notify("Task updated successfully", type="positive")
            self.on_click_select_task(task_data)
            dialog.close()
            self.render_content.refresh()
        except Exception as e:
            print(f"Error updating task: {str(e)}")
            ui.notify("Error updating task", type="negative")

    @ui.refreshable
    def render_content(self):
        tasks = self.state["tasks"]
        grid_data = self._format_grid_data(tasks)

        grid = ui.aggrid(
            {
                "columnDefs": [
                    {"headerName": "Title", "field": "title", "flex": 2},
                    {
                        "headerName": "Description",
                        "field": "description",
                        "flex": 3,
                    },
                    {"headerName": "Due Date", "field": "due_date", "flex": 2},
                    {"headerName": "Status", "field": "status", "flex": 1},
                    {"headerName": "Priority", "field": "priority", "flex": 1},
                ],
                "rowData": grid_data,
                "defaultColDef": {
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                },
                "rowSelection": "single",
                "theme": "material",
            }
        ).classes("h-[70vh]")

        grid.on("cellClicked", self._on_row_clicked)

    def render(self):
        with ui.card().style(self.style_manager.get_style("list_view.card")):
            self.render_content()
