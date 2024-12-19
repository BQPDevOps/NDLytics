from nicegui import ui
from modules import StyleManager
from models import GoalModel
from middleware.dynamo import DynamoMiddleware
from middleware.cognito import CognitoMiddleware
import uuid
from config import config
from datetime import datetime
from utils.helpers import *
from icecream import ic


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


class NewGoalInput:
    def __init__(self):
        self.goal_name = ""
        self.description = ""
        self.priority = 1
        self.due_date = ""
        self.status = "pending"


class GoalTableComponent:
    def __init__(self, session_manager, state, on_click_select_goal):
        self.session_manager = session_manager
        self.state = state
        self.on_click_select_goal = on_click_select_goal
        self.style_manager = StyleManager()
        self.cognito_middleware = CognitoMiddleware()
        self.dynamo_middleware = DynamoMiddleware(config.aws_users_table_name)
        self.goal_input = NewGoalInput()
        self._config()
        self.user_record = self._get_user_record()
        # Extract goals from user record, default to empty list if not found
        self.user_goals = (
            self.user_record.get("goals", {}).get("L", []) if self.user_record else []
        )

    def _config(self):

        self.style_manager.set_styles(
            {
                "goal_table_component": {
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
                    "add_goal_modal_header_container": """
                    display:flex;
                    width:100%;
                    height:4.5rem;
                    margin-bottom:1rem;
                    """,
                    "add_goal_modal_input_container": """
                    width:100%;
                    padding-top:0.5rem;
                    height:30rem;
                    """,
                }
            }
        )

    def _get_user_record(self):
        # Get current user ID from Cognito
        user_id = self.cognito_middleware.get_user_id()

        # Get username from storage
        username = self.session_manager.get_from_storage("username")

        # Get company_id from Cognito attributes
        company_id = self.cognito_middleware.get_all_custom_attributes(username).get(
            "custom:company_id"
        )

        # Create the key for DynamoDB query with both partition and sort key
        key = {"user_id": {"S": user_id}, "company_id": {"S": company_id}}

        # Get user record from DynamoDB
        try:
            user_record = self.dynamo_middleware.get_item(key)
            return user_record if user_record else None
        except Exception as e:
            ic(f"Error getting user record: {e}")
            return None

    def _open_add_goal_modal(self):
        dialog = ui.dialog().props("medium")
        with dialog, ui.card().classes("w-full"):
            with ui.row().classes("w-full"):
                ui.label("Add New Goal").style(
                    "font-size:1.2rem;font-weight:bold;color:#4A4A4A;"
                )
            with ui.column().style(
                self.style_manager.get_style(
                    "goal_table_component.add_goal_modal_header_container"
                )
            ):
                ui.input(placeholder="goal name...").props("outlined dense").classes(
                    "w-full"
                ).bind_value(self.goal_input, "goal_name")
                with ui.row().classes("w-full flex justify-end flex-row"):
                    with ui.column().classes("flex-grow"):
                        ui.select({1: "Low", 2: "Medium", 3: "High"}).props(
                            "outlined dense"
                        ).classes("w-full").bind_value(self.goal_input, "priority")
                    with ui.column():
                        with ui.input("Date").props("outlined dense") as date:
                            with ui.menu().props("no-parent-event") as menu:
                                with ui.date().bind_value(date).bind_value(
                                    self.goal_input, "due_date"
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
                    "goal_table_component.add_goal_modal_input_container"
                )
            ):
                ui.editor(placeholder="goal description...").style(
                    "height:100%;width:100%;"
                ).bind_value(self.goal_input, "description")
            with ui.row().classes("w-full flex justify-end flex-row"):
                ui.button(
                    "Cancel", on_click=lambda: self._reset_and_close(dialog)
                ).props("flat")
                ui.button("Add", on_click=lambda: self._add_goal(dialog)).props("flat")

        dialog.open()

    def _add_goal(self, dialog):
        user_id = self.cognito_middleware.get_user_id()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        # Convert due_date to string if it's a datetime object
        due_date = self.goal_input.due_date
        if isinstance(due_date, datetime):
            due_date = due_date.strftime("%Y-%m-%d %H:%M:%S.%f")

        # Create new goal in DynamoDB format
        new_goal = {
            "M": {
                "goal_id": {"S": str(uuid.uuid4())},
                "goal_name": {"S": self.goal_input.goal_name},
                "goal_description": {"S": self.goal_input.description},
                "goal_priority": {"N": str(self.goal_input.priority)},
                "goal_due_date": {"S": due_date},
                "goal_status": {"S": self.goal_input.status},
                "goal_create_on": {"S": current_time},
                "goal_created_by": {"S": user_id},
                "goal_updated_on": {"S": current_time},
                "goal_updated_by": {"S": user_id},
                "goal_assigned_to": {"L": [{"S": user_id}]},
                "goal_comments": {"L": []},
            }
        }

        # Get the current user record
        user_record = self._get_user_record()
        if not user_record:
            ic("No user record found")
            return

        # Create the key for DynamoDB update
        key = {
            "user_id": {"S": user_id},
            "company_id": {"S": user_record.get("company_id", {}).get("S")},
        }

        # Update expression to append the new goal to the goals list
        update_expression = (
            "SET goals = list_append(if_not_exists(goals, :empty_list), :new_goal)"
        )
        expression_values = {":new_goal": {"L": [new_goal]}, ":empty_list": {"L": []}}

        try:
            # Update the user record in DynamoDB
            self.dynamo_middleware.update_item(
                key=key,
                update_expression=update_expression,
                expression_attribute_values=expression_values,
            )

            # Update local user_goals list
            self.user_goals.append(new_goal)

            # Reset the input form and close dialog
            self.goal_input = NewGoalInput()
            dialog.close()

            # Convert the new goal to regular format and select it
            formatted_goal = dynamo_to_json(new_goal)
            self.on_click_select_goal(formatted_goal)

        except Exception as e:
            ic(f"Error updating user record: {e}")

    def _reset_and_close(self, dialog):
        self.goal_input = NewGoalInput()
        dialog.close()

    def render(self):
        goals = self.user_goals
        formatted_goals = [dynamo_to_json(goal) for goal in goals]

        with ui.column().classes("w-full h-full"):
            with ui.row().style(
                self.style_manager.get_style("goal_table_component.title_container")
            ):
                with ui.column().classes("flex-grow justify-center"):
                    ui.label("Goals")
                with ui.column().classes("flex flex-grow items-end justify-center"):
                    ui.button(icon="add", on_click=self._open_add_goal_modal).props(
                        "round size=sm"
                    )
            with ui.column().classes("w-full h-[76vh]"):
                with ui.list().classes("w-full"):
                    with ui.item():
                        with ui.row().classes("w-full"):
                            ui.label("Goal Name").style(
                                "font-size:1.2rem;font-weight:bold;color:#4A4A4A;"
                            )
                        with ui.row().classes("w-full"):
                            ui.label("Goal Description").style(
                                "font-size:1rem;color:#4A4A4A;"
                            )
                        with ui.row().classes("w-full"):
                            ui.label("Goal Due Date").style(
                                "font-size:1rem;color:#4A4A4A;"
                            )
                        with ui.row().classes("w-full"):
                            ui.label("Goal Status").style(
                                "font-size:1rem;color:#4A4A4A;"
                            )
                        with ui.row().classes("w-full"):
                            ui.label("Goal Priority").style(
                                "font-size:1rem;color:#4A4A4A;"
                            )
                    with ui.scroll_area().classes("w-full h-[76vh]"):
                        with ui.list().props("bordered separator").classes(
                            "w-full h-full"
                        ):
                            for goal in formatted_goals:
                                with ui.item(
                                    on_click=lambda: self.on_click_select_goal(goal)
                                ):
                                    with ui.row().classes("w-full"):
                                        ui.label(
                                            truncate_text(goal["goal_name"], 30)
                                        ).style(
                                            "font-size:1.2rem;font-weight:bold;color:#4A4A4A;"
                                        )
                                    with ui.row().classes("w-full"):
                                        ui.label(
                                            truncate_text(goal["goal_description"], 100)
                                        ).style("font-size:1rem;color:#4A4A4A;")
                                    with ui.row().classes("w-full"):
                                        ui.label(
                                            format_date(goal["goal_due_date"])
                                        ).style("font-size:1rem;color:#4A4A4A;")
                                    with ui.row().classes("w-full"):
                                        ui.label(goal["goal_status"]).style(
                                            "font-size:1rem;color:#4A4A4A;"
                                        )
                                    with ui.row().classes("w-full"):
                                        ui.label(
                                            format_priority(int(goal["goal_priority"]))
                                        ).style("font-size:1rem;color:#4A4A4A;")
