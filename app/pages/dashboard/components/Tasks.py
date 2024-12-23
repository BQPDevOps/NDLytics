from nicegui import ui
from modules import TokenManager, TokenType
from icecream import ic
from middleware.cognito import CognitoMiddleware
from middleware.dynamo import DynamoMiddleware
from modules import StyleManager
from models import TaskModel
from datetime import datetime
from utils.helpers import *
from config import config
import asyncio
import uuid


class TasksComponent:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.cognito_middleware = CognitoMiddleware()
        self.dynamo_middleware = DynamoMiddleware(config.aws_tasks_table_name)
        self.attributes = self._load_user_data()
        self.style_manager = StyleManager()
        self._component_config()

    def _component_config(self):
        self.style_manager.set_styles(
            {
                "todo_component": {
                    "title_container": """
                    display:flex;
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
                    "title_text": """
                    font-size:1.2rem;
                    font-weight:bold;
                    color:#4A4A4A;
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

    def _load_user_data(self):
        id_token = self.session_manager.get_from_storage("id_token")
        token_manager = TokenManager(TokenType.ID, id_token)
        user_data = token_manager.get_decoded_token()
        attributes = self.cognito_middleware.get_all_custom_attributes(user_data.sub)
        return attributes

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

    @ui.refreshable
    def render_tasks_list(self, tasks_data, is_today=True):
        try:
            if tasks_data:
                for task in tasks_data:
                    self._render_task_item(task)
            else:
                with ui.column().classes("w-full p-4 text-center"):
                    message = "No tasks due today" if is_today else "No upcoming tasks"
                    ui.label(message).style("color: #666; font-style: italic;")
        except Exception as e:
            print(f"Error rendering tasks list: {str(e)}")
            with ui.column().classes("w-full p-4 text-center"):
                ui.label("Unable to load tasks").style(
                    "color: #666; font-style: italic;"
                )

    def render(self):
        try:
            tasks = self._get_tasks()
            formatted_tasks = [dynamo_to_json(task) for task in tasks]
            today = datetime.now().date()

            today_tasks = []
            future_tasks = []

            for task in formatted_tasks:
                try:
                    task_date = datetime.strptime(
                        task["task_due_date"].split()[0], "%Y-%m-%d"
                    ).date()
                    if task["task_status"].lower() == "pending":
                        if task_date.strftime("%Y-%m-%d") == today.strftime("%Y-%m-%d"):
                            today_tasks.append(task)
                        elif task_date > today:
                            future_tasks.append(task)
                except Exception as e:
                    print(f"Error processing task: {task}")
                    print(f"Error: {str(e)}")

            # Today's Tasks Card
            with ui.card().classes("w-full flex flex-col mb-4"):
                with ui.row().style(
                    self.style_manager.get_style("todo_component.title_container")
                ):
                    ui.label("Due Today").style(
                        self.style_manager.get_style("todo_component.title_text")
                    )
                    # ui.label(f"({len(today_tasks)})").style(
                    #     self.style_manager.get_style("todo_component.title_text")
                    # )
                    ui.space()
                    ui.button(icon="add", on_click=self.open_task_modal).props(
                        "round size=sm"
                    )

                with ui.column().classes("w-full"):
                    with ui.scroll_area().classes("w-full max-h-[300px]"):
                        self.render_tasks_list(today_tasks, is_today=True)

            # Future Tasks Card
            with ui.card().classes("w-full flex flex-col"):
                with ui.row().style(
                    self.style_manager.get_style("todo_component.title_container")
                ):
                    ui.label("Upcoming").style(
                        self.style_manager.get_style("todo_component.title_text")
                    )
                    ui.space()
                    ui.label(f"({len(future_tasks)})").style(
                        self.style_manager.get_style("todo_component.title_text")
                    )

                with ui.column().classes("w-full"):
                    with ui.scroll_area().classes("w-full max-h-[300px]"):
                        self.render_tasks_list(future_tasks, is_today=False)
        except Exception as e:
            print(f"Error in render: {str(e)}")
            with ui.column().classes("w-full p-4 text-center"):
                ui.label("Unable to load tasks").style(
                    "color: #666; font-style: italic;"
                )

    def _render_task_item(self, task_data):
        item_container = (
            ui.item()
            .classes("w-full h-[100%] rounded-lg transition-all duration-300 bg-white")
            .style(
                """
                gap:0;
                margin:0 0;
                border:1px solid rgba(192,192,192,0.3);
                box-shadow:0 0 0 1px rgba(192,192,192,0.3);
                position: relative;
                z-index: 1;
                """
            )
        )

        # Track completion timer
        completion_timer = None

        async def complete_task(task_info):
            # Animate item off screen
            item_container.style(add="transform: translateX(-100%);")
            await asyncio.sleep(0.3)  # Wait for animation

            # Update task in DynamoDB
            try:
                self.dynamo_middleware.update_item(
                    key={
                        "task_id": {"S": task_info["task_id"]},
                        "user_id": {"S": task_info["user_id"]},
                    },
                    update_expression="SET task_status = :status",
                    expression_attribute_values={":status": {"S": "Completed"}},
                )
                await ui.run_javascript("window.location.reload()")
            except Exception as e:
                print(f"Error updating task: {str(e)}")
                ui.notify("Error updating task status", type="negative")

        async def handle_undo():
            nonlocal completion_timer
            # Cancel the pending completion if it exists
            if completion_timer and not completion_timer.done():
                completion_timer.cancel()

            # Reset checkbox
            checkbox.value = False

            # Animate back to original position
            item_container.classes(remove="w-[calc(100%-3rem)]")
            item_container.classes(add="w-full")
            item_container.style(remove="transform: translateX(-4rem);")

        async def on_check_change(e):
            nonlocal completion_timer
            checked = e.value if isinstance(e, object) else e
            if checked:
                # Initial slide animation
                item_container.classes(remove="w-full")
                item_container.classes(add="w-[calc(100%-3rem)]")
                item_container.style(add="transform: translateX(-4rem);")

                # Wait for animation then start completion timer
                await asyncio.sleep(0.3)

                # Create new completion timer
                completion_timer = asyncio.create_task(asyncio.sleep(3))

                try:
                    await completion_timer
                    await complete_task(task_data)
                except asyncio.CancelledError:
                    # Timer was cancelled by undo
                    pass
            else:
                # Handle unchecking normally
                item_container.classes(remove="w-[calc(100%-3rem)]")
                item_container.classes(add="w-full")
                item_container.style(remove="transform: translateX(-4rem);")

        with item_container:
            with ui.row().classes("w-full h-[100%] flex items-center justify-center"):
                checkbox = ui.checkbox(
                    value=task_data["task_status"] == "Completed",
                    on_change=on_check_change,
                )
                with ui.item_section().classes("flex-grow gap-0 relative"):
                    ui.button("undo", on_click=handle_undo).props("flat").classes(
                        "absolute right-[-8rem] top-1/2 -translate-y-1/2"
                    )
                    with ui.row().classes("w-full justify-between"):
                        ui.label(truncate_text(task_data["task_name"], 30)).style(
                            "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                        )
                        ui.label(
                            datetime.strptime(
                                task_data["task_due_date"], "%Y-%m-%d %H:%M:%S"
                            ).strftime("%m-%d-%Y")
                        ).style("font-size:1rem;color:#4A4A4A;padding-right:0.2rem")
                    with ui.row().classes("w-full flex-grow justify-end"):
                        with ui.row():
                            status = task_data["task_status"].lower()
                            color = {
                                "completed": "green",
                                "pending": "orange",
                                "overdue": "red",
                            }.get(status, "grey")
                            ui.chip(
                                task_data["task_status"],
                                color=color,
                                text_color="white",
                            ).classes("text-md").props("dense")

    def open_task_modal(self):
        with ui.dialog().props("medium") as dialog:
            with ui.card().classes("w-full"):
                with ui.row().classes("w-full"):
                    ui.label("Add New Task").style(
                        "font-size:1.2rem;font-weight:bold;color:#4A4A4A;"
                    )
                with ui.column().style(
                    self.style_manager.get_style(
                        "todo_component.add_task_modal_header_container"
                    )
                ):
                    task_name = (
                        ui.input(placeholder="Task title")
                        .props("outlined dense")
                        .classes("w-full")
                    )

                    with ui.row().classes("w-full flex justify-end flex-row"):
                        with ui.column().classes("flex-grow"):
                            priority = (
                                ui.select({1: "Low", 2: "Medium", 3: "High"}, value=1)
                                .props("outlined dense")
                                .classes("w-full")
                            )

                        with ui.column():
                            with ui.input("Date").props("outlined dense") as date:
                                with ui.menu().props("no-parent-event") as menu:
                                    with ui.date().bind_value(date):
                                        with ui.row().classes("justify-end"):
                                            ui.button(
                                                "Close", on_click=menu.close
                                            ).props("flat")
                                    with date.add_slot("append"):
                                        ui.icon("edit_calendar").on(
                                            "click", menu.open
                                        ).classes("cursor-pointer")

                # Add description editor
                with ui.column().style(
                    self.style_manager.get_style(
                        "todo_component.add_task_modal_input_container"
                    )
                ):
                    description = ui.editor(placeholder="Task description").style(
                        "height:100%;width:100%;"
                    )

                with ui.row().classes("w-full flex justify-between items-center mt-4"):
                    assigned_users = (
                        ui.select(
                            options=self._get_users(),
                            with_input=True,
                            multiple=True,
                            label="Assign Users",
                        )
                        .props("outlined dense use-chips")
                        .classes("w-[40%]")
                    )
                    with ui.row().classes("gap-2"):
                        ui.button("Cancel", on_click=dialog.close).props("flat")
                        ui.button(
                            "Add",
                            on_click=lambda: self._add_task(
                                dialog,
                                task_name.value,
                                priority.value,
                                date.value,
                                description.value,
                                assigned_users.value,
                            ),
                        ).props("flat")
                dialog.open()

    def _add_task(
        self, dialog, task_name, priority, due_date, description="", assigned_users=[]
    ):
        try:
            if not task_name:
                ui.notify("Task name is required", type="warning")
                return

            user_id = self.cognito_middleware.get_user_id()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Format due date properly
            if not due_date:
                due_date = current_time
            elif isinstance(due_date, datetime):
                due_date = due_date.replace(hour=0, minute=0, second=0).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            else:
                # If it's just a date string, append the time
                due_date = f"{due_date} 00:00:00"

            # If no users assigned, assign to creator
            if not assigned_users:
                assigned_users = [user_id]

            item = {
                "task_id": {"S": str(uuid.uuid4())},
                "user_id": {"S": user_id},
                "task_name": {"S": task_name},
                "task_description": {"S": description},
                "task_priority": {"N": str(priority)},
                "task_due_date": {"S": str(due_date)},
                "task_status": {"S": "pending"},
                "task_create_on": {"S": current_time},
                "task_created_by": {"S": user_id},
                "task_updated_on": {"S": current_time},
                "task_updated_by": {"S": user_id},
                "task_assigned_to": {"L": [{"S": user_id}]},
                "task_comments": {"L": []},
                "task_tags": {"L": [{"S": str(user_id)} for user_id in assigned_users]},
            }

            self.dynamo_middleware.put_item(item)
            dialog.close()
            ui.notify("Task added successfully", type="positive")
            # Get updated tasks and refresh the view
            tasks = self._get_tasks()
            formatted_tasks = [dynamo_to_json(task) for task in tasks]
            self.render_tasks_list.refresh()
            # Refresh the entire component to update task counts
            ui.run_javascript("window.location.reload()")
        except Exception as e:
            print(f"Error adding task: {str(e)}")
            ui.notify("Error adding task", type="negative")


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
