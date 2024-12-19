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
                }
            }
        )

    def _load_user_data(self):
        id_token = self.session_manager.get_from_storage("id_token")
        token_manager = TokenManager(TokenType.ID, id_token)
        user_data = token_manager.get_decoded_token()
        attributes = self.cognito_middleware.get_all_custom_attributes(user_data.sub)
        return attributes

    def _get_tasks(self):
        user_id = self.cognito_middleware.get_user_id()

        # Create expression for querying by user_id
        expression_values = {":uid": {"S": user_id}}

        # Get tasks for current user
        response = self.dynamo_middleware.scan(
            filter_expression="user_id = :uid",
            expression_attribute_values=expression_values,
        )

        return response["Items"] if "Items" in response else []

    def render(self):
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
                ui.label(f"Due Today").style(
                    self.style_manager.get_style("todo_component.title_text")
                )
                ui.space()
                ui.label(f"({len(today_tasks)})").style(
                    self.style_manager.get_style("todo_component.title_text")
                )
            if today_tasks:
                with ui.column().classes("w-full"):
                    with ui.scroll_area().classes("w-full max-h-[300px]"):
                        with ui.list().props("bordered separator").classes("w-full"):
                            for task in today_tasks:
                                self._render_task_item(task)
            else:
                with ui.column().classes("w-full p-4 text-center"):
                    ui.label("No tasks due today").style(
                        "color: #666; font-style: italic;"
                    )

        # Future Tasks Card
        with ui.card().classes("w-full flex flex-col"):
            with ui.row().style(
                self.style_manager.get_style("todo_component.title_container")
            ):
                ui.label(f"Upcoming Tasks").style(
                    self.style_manager.get_style("todo_component.title_text")
                )
                ui.space()
                ui.label(f"({len(future_tasks)})").style(
                    self.style_manager.get_style("todo_component.title_text")
                )
            with ui.column().classes("w-full flex-grow"):
                with ui.scroll_area().classes("w-full flex-grow"):
                    with ui.list().props("bordered separator").classes("w-full h-full"):
                        for task in future_tasks:
                            self._render_task_item(task)

    def _render_task_item(self, task):
        with ui.item().classes("w-full h-[100%]"):
            with ui.row().classes("w-full h-[100%]"):
                with ui.item_section().props("side"):
                    ui.checkbox(value=task["task_status"] == "Completed")
                with ui.item_section().classes("flex-grow gap-0"):
                    with ui.row().classes("w-full justify-between"):
                        ui.label(truncate_text(task["task_name"], 30)).style(
                            "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                        )
                        ui.label(
                            datetime.strptime(
                                task["task_due_date"], "%Y-%m-%d %H:%M:%S"
                            ).strftime("%m-%d-%Y")
                        ).style("font-size:0.8rem;color:#4A4A4A;")
                    with ui.row().classes("w-full flex-grow justify-end"):
                        with ui.row():
                            ui.label(task["task_status"]).style(
                                "font-size:1rem;color:#4A4A4A;"
                            )


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
