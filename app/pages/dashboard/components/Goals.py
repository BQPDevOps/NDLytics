from nicegui import ui
from modules import StyleManager, TokenManager, TokenType
from middleware.cognito import CognitoMiddleware
from middleware.dynamo import DynamoMiddleware
from datetime import datetime
from config import config


def truncate_text(text: str, max_length: int = 50) -> str:
    return text[:max_length] + "..." if len(text) > max_length else text


def dynamo_to_json(item):
    result = {}
    for key, value in item.items():
        # Extract the actual value from the DynamoDB format
        for val_type, val in value.items():
            result[key] = val
    return result


def format_date(date_str: str) -> str:
    try:
        if not date_str or date_str == "0-0-0":
            return "No date set"
        date_obj = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
        return date_obj.strftime("%m-%d-%Y")
    except (ValueError, AttributeError):
        return "Invalid date"


class GoalsComponent:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.cognito_middleware = CognitoMiddleware()
        self.dynamo_middleware = DynamoMiddleware(config.aws_users_table_name)
        self.attributes = self._load_user_data()
        self.style_manager = StyleManager()
        self._config()
        self.user_record = self._get_user_record()
        self.user_goals = (
            self.user_record.get("goals", {}).get("L", []) if self.user_record else []
        )

    def _config(self):
        self.style_manager.set_styles(
            {
                "goals_component": {
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

    def _get_user_record(self):
        try:
            # Get current user ID from Cognito
            user_id = self.cognito_middleware.get_user_id()
            if not user_id:
                print("Could not get user_id")
                return None

            # Get username from storage
            username = self.session_manager.get_from_storage("username")
            if not username:
                print("Could not get username from storage")
                return None

            # Get company_id from Cognito attributes
            attributes = self.cognito_middleware.get_all_custom_attributes(username)
            company_id = attributes.get("custom:company_id")
            if not company_id:
                print(f"No company_id found for user {username}")
                return None

            # Create the key for DynamoDB query
            key = {"user_id": {"S": user_id}, "company_id": {"S": company_id}}

            # Get user record from DynamoDB
            try:
                user_record = self.dynamo_middleware.get_item(key)
                return user_record if user_record else None
            except Exception as e:
                print(f"Error getting user record from DynamoDB: {e}")
                return None

        except Exception as e:
            print(f"Error in _get_user_record: {e}")
            return None

    def render(self):
        goals = self.user_goals
        formatted_goals = [dynamo_to_json(goal["M"]) for goal in goals]
        active_goals = []
        completed_goals = []

        for goal in formatted_goals:
            if goal.get("goal_status", "").lower() == "pending":
                active_goals.append(goal)
            elif goal.get("goal_status", "").lower() == "completed":
                completed_goals.append(goal)

        with ui.card().classes("w-full flex flex-col mb-4"):
            with ui.row().style(
                self.style_manager.get_style("goals_component.title_container")
            ):
                ui.label("Active Goals").style(
                    self.style_manager.get_style("goals_component.title_text")
                )
                ui.space()
                ui.label(f"({len(active_goals)})").style(
                    self.style_manager.get_style("goals_component.title_text")
                )

            if active_goals:
                with ui.column().classes("w-full"):
                    with ui.scroll_area().classes("w-full max-h-[300px]"):
                        with ui.list().props("bordered separator").classes("w-full"):
                            for goal in active_goals:
                                self._render_goal_item(goal)
            else:
                with ui.column().classes("w-full p-4 text-center"):
                    ui.label("No active goals").style(
                        "color: #666; font-style: italic;"
                    )

    def _render_goal_item(self, goal):
        with ui.item().classes("w-full h-[100%]"):
            with ui.row().classes("w-full h-[100%]"):
                with ui.item_section().props("side"):
                    ui.checkbox(
                        value=goal.get("goal_status", "").lower() == "completed"
                    )
                with ui.item_section().classes("flex-grow gap-0"):
                    with ui.row().classes("w-full justify-between"):
                        ui.label(
                            truncate_text(goal.get("goal_name", "Untitled"), 30)
                        ).style("font-size:1rem;font-weight:bold;color:#4A4A4A;")
                        ui.label(format_date(goal.get("goal_due_date", ""))).style(
                            "font-size:0.8rem;color:#4A4A4A;"
                        )
                    with ui.row().classes("w-full flex-grow justify-end"):
                        with ui.row():
                            ui.label(goal.get("goal_status", "Unknown")).style(
                                "font-size:1rem;color:#4A4A4A;"
                            )
