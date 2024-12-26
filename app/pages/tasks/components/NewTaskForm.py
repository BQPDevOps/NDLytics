from nicegui import ui
from datetime import datetime
from middleware.dynamo import DynamoMiddleware
from middleware.cognito import CognitoMiddleware
from config import config
import uuid


class NewTaskFormComponent:
    def __init__(self, on_task_created=None):
        self.on_task_created = on_task_created
        self.dynamo_middleware = DynamoMiddleware(config.aws_tasks_table_name)
        self.cognito_middleware = CognitoMiddleware()
        self._reset_form()

    def _get_users(self):
        users = self.cognito_middleware.get_users()
        formatted_users = {}
        for user in users:
            attributes = {
                attr["Name"]: attr["Value"] for attr in user.get("Attributes", [])
            }
            if "given_name" in attributes and "family_name" in attributes:
                user_id = user["Username"]
                name = f"{attributes['given_name']} {attributes['family_name'][0]}"
                formatted_users[user_id] = name
        return formatted_users

    def _create_task(self, dialog):
        try:
            if (
                not self.task["task_name"].strip()
                or not self.task["task_description"].strip()
            ):
                ui.notify("Title and description are required", type="warning")
                return

            user_id = self.cognito_middleware.get_user_id()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

            due_date = self.task["task_due_date"]
            if isinstance(due_date, datetime):
                due_date = due_date.strftime("%Y-%m-%d %H:%M:%S.%f")

            assigned_users = self.task["assigned_users"]
            if not assigned_users:
                assigned_users = [user_id]

            item = {
                "task_id": {"S": str(uuid.uuid4())},
                "user_id": {"S": user_id},
                "task_name": {"S": self.task["task_name"]},
                "task_description": {"S": self.task["task_description"]},
                "task_priority": {"N": str(self.task["task_priority"])},
                "task_due_date": {"S": due_date},
                "task_status": {"S": self.task["task_status"]},
                "task_create_on": {"S": current_time},
                "task_created_by": {"S": user_id},
                "task_updated_on": {"S": current_time},
                "task_updated_by": {"S": user_id},
                "task_assigned_to": {
                    "L": [{"S": str(user)} for user in assigned_users]
                },
                "task_comments": {"L": []},
                "task_tags": {"L": [{"S": str(user)} for user in assigned_users]},
            }

            self.dynamo_middleware.put_item(item)
            ui.notify("Task created successfully", type="positive")

            if self.on_task_created:
                self.on_task_created()

            dialog.close()

        except Exception as e:
            print(f"Error creating task: {str(e)}")
            ui.notify("Error creating task", type="negative")

    def _reset_form(self):
        current_date = datetime.now().strftime("%Y-%m-%d")
        self.task = {
            "task_name": "",
            "task_description": "",
            "task_priority": 1,
            "task_due_date": current_date,
            "task_status": "pending",
            "assigned_users": [],
        }

    def open(self):
        self._reset_form()

        dialog = ui.dialog().props("medium")
        with dialog, ui.card().classes("w-full"):
            with ui.row().classes("w-full"):
                ui.label("Create New Task").style(
                    "font-size:1.2rem;font-weight:bold;color:#4A4A4A;"
                )

            with ui.column().classes("w-full pt-4"):
                title_input = (
                    ui.input(placeholder="task name...")
                    .props("outlined dense autofocus")
                    .classes("w-full")
                    .bind_value(self.task, "task_name")
                )

                with ui.row().classes("w-full flex justify-end flex-row pt-2"):
                    with ui.column().classes("flex-grow"):
                        ui.select({1: "Low", 2: "Medium", 3: "High"}).props(
                            "outlined dense"
                        ).classes("w-full").bind_value(self.task, "task_priority")
                    with ui.column():
                        with ui.input("Date").props("outlined dense").bind_value(
                            self.task, "task_due_date"
                        ) as date:
                            with ui.menu().props("no-parent-event") as menu:
                                with ui.date().bind_value(date).bind_value(
                                    self.task, "task_due_date"
                                ).props('mask="YYYY-MM-DD"'):
                                    with ui.row().classes("justify-end"):
                                        ui.button("Close", on_click=menu.close).props(
                                            "flat"
                                        )
                            with date.add_slot("append"):
                                ui.icon("edit_calendar").on("click", menu.open).classes(
                                    "cursor-pointer"
                                )

            with ui.column().classes("w-full pt-4"):
                ui.editor(placeholder="task description...").style(
                    "height:30rem;width:100%;"
                ).bind_value(self.task, "task_description")

            with ui.row().classes("w-full flex justify-between items-center mt-4"):
                ui.select(
                    options=self._get_users(),
                    with_input=True,
                    multiple=True,
                    label="Assign Users",
                ).props("outlined dense use-chips").classes("w-[40%]").bind_value(
                    self.task, "assigned_users"
                )
                with ui.row().classes("gap-2"):
                    ui.button(
                        "Cancel", on_click=lambda: [self._reset_form(), dialog.close()]
                    ).props("flat")
                    ui.button(
                        "Create", on_click=lambda: self._create_task(dialog)
                    ).props("flat")

        dialog.open()
