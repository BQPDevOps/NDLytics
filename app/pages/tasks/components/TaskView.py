from nicegui import ui
from icecream import ic
from models import TaskModel
from datetime import datetime
from middleware.dynamo import DynamoMiddleware
from config import config


class TaskViewComponent:
    def __init__(self, state):
        self.state = state
        self.task = state["selected_task"]
        self.dynamo_middleware = DynamoMiddleware(config.aws_tasks_table_name)

    def _update_task(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        due_date = self.task["task_due_date"]
        if isinstance(due_date, datetime):
            due_date = due_date.strftime("%Y-%m-%d %H:%M:%S.%f")

        key = {
            "task_id": {"S": self.task["task_id"]},
            "user_id": {"S": self.task["user_id"]},
        }

        update_expr = """SET
            task_name = :name,
            task_description = :desc,
            task_priority = :priority,
            task_due_date = :due_date,
            task_status = :status,
            task_updated_on = :updated_on"""

        expr_values = {
            ":name": {"S": self.task["task_name"]},
            ":desc": {"S": self.task["task_description"]},
            ":priority": {"N": str(self.task["task_priority"])},
            ":due_date": {"S": due_date},
            ":status": {"S": self.task["task_status"]},
            ":updated_on": {"S": current_time},
        }

        self.dynamo_middleware.update_item(key, update_expr, expr_values)

    def render(self):
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full"):
                ui.label("Update Task").style(
                    "font-size:1.2rem;font-weight:bold;color:#4A4A4A;"
                )

            with ui.column().classes("w-full"):
                ui.input(placeholder="task name...").props("outlined dense").classes(
                    "w-full"
                ).bind_value(self.task, "task_name")

                with ui.row().classes("w-full flex justify-end flex-row"):
                    with ui.column().classes("flex-grow"):
                        ui.select({1: "Low", 2: "Medium", 3: "High"}).props(
                            "outlined dense"
                        ).classes("w-full").bind_value(self.task, "task_priority")
                    with ui.column():
                        with ui.input("Date").props("outlined dense") as date:
                            with ui.menu().props("no-parent-event") as menu:
                                with ui.date().bind_value(date).bind_value(
                                    self.task, "task_due_date"
                                ):
                                    with ui.row().classes("justify-end"):
                                        ui.button("Close", on_click=menu.close).props(
                                            "flat"
                                        )
                            with date.add_slot("append"):
                                ui.icon("edit_calendar").on("click", menu.open).classes(
                                    "cursor-pointer"
                                )

            with ui.column().classes("w-full pt-2"):
                ui.editor(placeholder="task description...").style(
                    "height:30rem;width:100%;"
                ).bind_value(self.task, "task_description")

            with ui.row().classes("w-full flex justify-end flex-row"):
                ui.button("Update", on_click=self._update_task).props("flat")
