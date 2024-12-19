from nicegui import ui
from icecream import ic
from datetime import datetime
from middleware.dynamo import DynamoMiddleware
from middleware.cognito import CognitoMiddleware
from config import config


class GoalViewComponent:
    def __init__(self, session_manager, state, on_click_select_goal):
        self.session_manager = session_manager
        self.state = state
        self.goal = state["selected_goal"]
        self.dynamo_middleware = DynamoMiddleware(config.aws_users_table_name)
        self.cognito_middleware = CognitoMiddleware()
        self.on_click_select_goal = on_click_select_goal

    def _update_goal(self):
        # Get current user info
        user_id = self.cognito_middleware.get_user_id()
        username = self.session_manager.get_from_storage("username")
        company_id = self.cognito_middleware.get_all_custom_attributes(username).get(
            "custom:company_id"
        )
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        # Format due date
        due_date = self.goal["goal_due_date"]
        if isinstance(due_date, datetime):
            due_date = due_date.strftime("%Y-%m-%d %H:%M:%S.%f")

        # Create updated goal in DynamoDB format
        updated_goal = {
            "M": {
                "goal_id": {"S": self.goal["goal_id"]},
                "goal_name": {"S": self.goal["goal_name"]},
                "goal_description": {"S": self.goal["goal_description"]},
                "goal_priority": {"N": str(self.goal["goal_priority"])},
                "goal_due_date": {"S": due_date},
                "goal_status": {"S": self.goal["goal_status"]},
                "goal_create_on": {"S": self.goal["goal_create_on"]},
                "goal_created_by": {"S": self.goal["goal_created_by"]},
                "goal_updated_on": {"S": current_time},
                "goal_updated_by": {"S": user_id},
                "goal_assigned_to": {"L": [{"S": user_id}]},
                "goal_comments": {"L": self.goal.get("goal_comments", [])},
            }
        }

        # Create key for DynamoDB
        key = {"user_id": {"S": user_id}, "company_id": {"S": company_id}}

        try:
            # Get current user record to find goal index
            user_record = self.dynamo_middleware.get_item(key)
            if not user_record or "goals" not in user_record:
                ic("No user record or goals found")
                return

            goals = user_record["goals"]["L"]
            goal_index = next(
                (
                    i
                    for i, g in enumerate(goals)
                    if g["M"]["goal_id"]["S"] == self.goal["goal_id"]
                ),
                None,
            )

            if goal_index is None:
                ic("Goal not found in user record")
                return

            # Update specific goal in the goals array
            update_expression = f"SET goals[{goal_index}] = :updated_goal"
            expression_values = {":updated_goal": updated_goal}

            # Update the user record in DynamoDB
            self.dynamo_middleware.update_item(
                key=key,
                update_expression=update_expression,
                expression_attribute_values=expression_values,
            )

            # Clear selected goal after successful update
            self.on_click_select_goal(None)

        except Exception as e:
            ic(f"Error updating goal: {e}")

    def render(self):
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full"):
                ui.label("Update Goal").style(
                    "font-size:1.2rem;font-weight:bold;color:#4A4A4A;"
                )

            with ui.column().classes("w-full"):
                ui.input(placeholder="goal name...").props("outlined dense").classes(
                    "w-full"
                ).bind_value(self.goal, "goal_name")

                with ui.row().classes("w-full flex justify-end flex-row"):
                    with ui.column().classes("flex-grow"):
                        ui.select({1: "Low", 2: "Medium", 3: "High"}).props(
                            "outlined dense"
                        ).classes("w-full").bind_value(self.goal, "goal_priority")
                    with ui.column():
                        with ui.input("Date").props("outlined dense") as date:
                            with ui.menu().props("no-parent-event") as menu:
                                with ui.date().bind_value(date).bind_value(
                                    self.goal, "goal_due_date"
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
                ui.editor(placeholder="goal description...").style(
                    "height:30rem;width:100%;"
                ).bind_value(self.goal, "goal_description")

            with ui.row().classes("w-full flex justify-end flex-row"):
                ui.button("Update", on_click=self._update_goal).props("flat")
