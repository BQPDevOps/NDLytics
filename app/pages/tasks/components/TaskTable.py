from nicegui import ui
from modules import StyleManager
from models import TaskModel
from middleware.dynamo import DynamoMiddleware
from middleware.cognito import CognitoMiddleware
import uuid
from config import config
from datetime import datetime
from utils.helpers import *


class NewTaskInput:
    def __init__(self):
        self.task_name = ""
        self.description = ""
        self.priority = 1
        self.due_date = ""
        self.status = "pending"
        self.assigned_users = []


class TaskTableComponent:
    def __init__(self, state, on_click_select_task):
        self.state = state
        self.on_click_select_task = on_click_select_task
        self.style_manager = StyleManager()
        self.cognito_middleware = CognitoMiddleware()
        self.dynamo_middleware = DynamoMiddleware(config.aws_tasks_table_name)
        self.new_task_input = NewTaskInput()
        self._config()

    def _config(self):
        self.style_manager.set_styles(
            {
                "task_table_component": {
                    "title_container": """
                    display:flex;
                    justify-content:flex-end;
                    align-items:center;
                    padding-left:1rem;
                    padding-right:1rem;
                    width:100%;
                    height:2.5rem;
                    background-color:#FFFFFF;
                    border-radius:5px;
                    border:1px solid rgba(192,192,192,0.3);
                    box-shadow:0 0 0 1px rgba(192,192,192,0.4);
                    background-color:rgba(192,192,192,0.1);
                    """,
                    "add_task_modal_header_container": """
                    display:flex;
                    width:100%;
                    height:4.5rem;
                    margin-bottom:1rem;
                    """,
                    "add_task_modal_input_container": """
                    width:100%;
                    padding-top:0.5rem;
                    height:30rem;
                    """,
                }
            }
        )

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

    def _get_tasks(self):
        user_id = self.cognito_middleware.get_user_id()

        # Get user's own tasks
        own_tasks_expression = {":uid": {"S": user_id}}
        own_tasks_response = self.dynamo_middleware.scan(
            filter_expression="user_id = :uid",
            expression_attribute_values=own_tasks_expression,
        )

        # Get tasks where user is tagged
        tagged_tasks_expression = {":uid": {"S": user_id}}
        tagged_tasks_response = self.dynamo_middleware.scan(
            filter_expression="contains(task_tags, :uid)",
            expression_attribute_values=tagged_tasks_expression,
        )

        # Combine and deduplicate tasks
        all_tasks = []
        seen_task_ids = set()

        # Add own tasks
        if "Items" in own_tasks_response:
            for task in own_tasks_response["Items"]:
                task_id = task["task_id"]["S"]
                if task_id not in seen_task_ids:
                    all_tasks.append(task)
                    seen_task_ids.add(task_id)

        # Add tagged tasks
        if "Items" in tagged_tasks_response:
            for task in tagged_tasks_response["Items"]:
                task_id = task["task_id"]["S"]
                if task_id not in seen_task_ids:
                    all_tasks.append(task)
                    seen_task_ids.add(task_id)

        return all_tasks

    def _open_add_task_modal(self):
        dialog = ui.dialog().props("medium")
        with dialog, ui.card().classes("w-full"):
            with ui.row().classes("w-full"):
                ui.label("Add New Task").style(
                    "font-size:1.2rem;font-weight:bold;color:#4A4A4A;"
                )
            with ui.column().style(
                self.style_manager.get_style(
                    "task_table_component.add_task_modal_header_container"
                )
            ):
                ui.input(placeholder="task name...").props("outlined dense").classes(
                    "w-full"
                ).bind_value(self.new_task_input, "task_name")
                with ui.row().classes("w-full flex justify-end flex-row"):
                    with ui.column().classes("flex-grow"):
                        ui.select({1: "Low", 2: "Medium", 3: "High"}).props(
                            "outlined dense"
                        ).classes("w-full").bind_value(self.new_task_input, "priority")
                    with ui.column():
                        with ui.input("Date").props("outlined dense") as date:
                            with ui.menu().props("no-parent-event") as menu:
                                with ui.date().bind_value(date).bind_value(
                                    self.new_task_input, "due_date"
                                ):
                                    with ui.row().classes("justify-end"):
                                        ui.button("Close", on_click=menu.close).props(
                                            "flat"
                                        )
                            with date.add_slot("append"):
                                ui.icon("edit_calendar").on("click", menu.open).classes(
                                    "cursor-pointer"
                                )
            with ui.column().style(
                self.style_manager.get_style(
                    "task_table_component.add_task_modal_input_container"
                )
            ):
                ui.editor(placeholder="task description...").style(
                    "height:100%;width:100%;"
                ).bind_value(self.new_task_input, "description")
            with ui.row().classes("w-full flex justify-between items-center mt-4"):
                ui.select(
                    options=self._get_users(),
                    with_input=True,
                    multiple=True,
                    label="Assign Users",
                ).props("outlined dense use-chips").classes("w-[40%]").bind_value(
                    self.new_task_input, "assigned_users"
                )
                with ui.row().classes("gap-2"):
                    ui.button(
                        "Cancel", on_click=lambda: self._reset_and_close(dialog)
                    ).props("flat")
                    ui.button("Add", on_click=lambda: self._add_task(dialog)).props(
                        "flat"
                    )

        dialog.open()

    def _add_task(self, dialog):
        user_id = self.cognito_middleware.get_user_id()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        # Convert due_date to string before creating TaskModel
        due_date = self.new_task_input.due_date
        if isinstance(due_date, datetime):
            due_date = due_date.strftime("%Y-%m-%d %H:%M:%S.%f")

        # Get selected user IDs
        assigned_users = self.new_task_input.assigned_users
        if not assigned_users:
            assigned_users = [user_id]

        # Create task model
        task = TaskModel(
            task_id=str(uuid.uuid4()),
            user_id=user_id,
            task_name=self.new_task_input.task_name,
            task_description=self.new_task_input.description,
            task_priority=self.new_task_input.priority,
            task_due_date=due_date,
            task_status=self.new_task_input.status,
            task_create_on=current_time,
            task_created_by=user_id,
            task_updated_on=current_time,
            task_updated_by=user_id,
            task_assigned_to=[user_id],
            task_comments=[],
        )

        # Ensure all datetime fields are strings for DynamoDB
        item = {
            "task_id": {"S": str(task.task_id)},
            "user_id": {"S": str(task.user_id)},
            "task_name": {"S": str(task.task_name)},
            "task_description": {"S": str(task.task_description)},
            "task_priority": {"N": str(task.task_priority)},
            "task_due_date": {"S": str(task.task_due_date)},
            "task_status": {"S": str(task.task_status)},
            "task_create_on": {"S": str(task.task_create_on)},
            "task_created_by": {"S": str(task.task_created_by)},
            "task_updated_on": {"S": str(task.task_updated_on)},
            "task_updated_by": {"S": str(task.task_updated_by)},
            "task_assigned_to": {"L": [{"S": str(user_id)}]},
            "task_comments": {"L": []},
            "task_tags": {"L": [{"S": str(user_id)} for user_id in assigned_users]},
        }

        self.dynamo_middleware.put_item(item)
        self.new_task_input = NewTaskInput()
        dialog.close()

    def _reset_and_close(self, dialog):
        self.new_task_input = NewTaskInput()
        dialog.close()

    def render(self):
        tasks = self._get_tasks()
        formatted_tasks = [dynamo_to_json(task) for task in tasks]

        with ui.column().classes("w-full h-full"):
            with ui.row().style(
                self.style_manager.get_style("task_table_component.title_container")
            ):
                with ui.column().classes("flex-grow justify-center"):
                    ui.label("Tasks")
                with ui.column().classes("flex flex-grow items-end justify-center"):
                    ui.button(icon="add", on_click=self._open_add_task_modal).props(
                        "round size=sm"
                    )
            with ui.column().classes("w-full h-[76vh]"):
                with ui.list().classes("w-full"):
                    with ui.item():
                        with ui.row().classes("w-full"):
                            ui.label("Task Name").style(
                                "font-size:1.2rem;font-weight:bold;color:#4A4A4A;"
                            )
                        with ui.row().classes("w-full"):
                            ui.label("Task Description").style(
                                "font-size:1rem;color:#4A4A4A;"
                            )
                        with ui.row().classes("w-full"):
                            ui.label("Task Due Date").style(
                                "font-size:1rem;color:#4A4A4A;"
                            )
                        with ui.row().classes("w-full"):
                            ui.label("Task Status").style(
                                "font-size:1rem;color:#4A4A4A;"
                            )
                        with ui.row().classes("w-full"):
                            ui.label("Task Priority").style(
                                "font-size:1rem;color:#4A4A4A;"
                            )
                    with ui.scroll_area().classes("w-full h-[76vh]"):
                        with ui.list().props("bordered separator").classes(
                            "w-full h-full"
                        ):
                            for task in formatted_tasks:
                                with ui.item(
                                    on_click=lambda: self.on_click_select_task(task)
                                ):
                                    with ui.row().classes("w-full"):
                                        ui.label(
                                            truncate_text(task["task_name"], 30)
                                        ).style(
                                            "font-size:1.2rem;font-weight:bold;color:#4A4A4A;"
                                        )
                                    with ui.row().classes("w-full"):
                                        ui.label(
                                            truncate_text(task["task_description"], 100)
                                        ).style("font-size:1rem;color:#4A4A4A;")
                                    with ui.row().classes("w-full"):
                                        ui.label(
                                            format_date(task["task_due_date"])
                                        ).style("font-size:1rem;color:#4A4A4A;")
                                    with ui.row().classes("w-full"):
                                        ui.label(task["task_status"]).style(
                                            "font-size:1rem;color:#4A4A4A;"
                                        )
                                    with ui.row().classes("w-full"):
                                        ui.label(
                                            format_priority(int(task["task_priority"]))
                                        ).style("font-size:1rem;color:#4A4A4A;")


def format_priority(priority: int) -> str:
    priority_map = {1: "Low", 2: "Moderate", 3: "High"}
    return priority_map.get(priority, "Unknown")


def truncate_text(text: str, max_length: int = 50) -> str:
    return text[:max_length] + "..." if len(text) > max_length else text


def get_ordinal_suffix(day: int) -> str:
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return suffix


def format_date(date_str: str) -> str:
    try:
        if isinstance(date_str, datetime):
            date_obj = date_str
        else:
            # Handle the specific format from your data
            date_obj = datetime.strptime(date_str.split(".")[0], "%Y-%m-%d %H:%M:%S")

        day = date_obj.day
        suffix = get_ordinal_suffix(day)
        return date_obj.strftime(f"%A, %B {day}{suffix}")
    except (ValueError, AttributeError):
        return date_str
