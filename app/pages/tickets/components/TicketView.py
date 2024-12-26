from nicegui import ui
from datetime import datetime
from modules import StyleManager
from middleware.dynamo import DynamoMiddleware
from middleware.cognito import CognitoMiddleware
from config import config
from icecream import ic


class TicketViewComponent:
    def __init__(self, ticket_data, on_save=None, on_cancel=None):
        self.ticket = ticket_data.copy()  # Create a copy to track changes

        # Format ticket_comments from DynamoDB format if it exists
        if "ticket_comments" in self.ticket:
            raw_comments = self.ticket["ticket_comments"].get("L", [])
            self.ticket["ticket_comments"] = []
            for comment in raw_comments:
                comment_map = comment.get("M", {})
                if comment_map:  # Only add if we have a valid comment map
                    self.ticket["ticket_comments"].append(
                        {
                            "comment_id": comment_map.get("comment_id", {}).get(
                                "S", ""
                            ),
                            "user_id": comment_map.get("user_id", {}).get("S", ""),
                            "comment_text": comment_map.get("comment_text", {}).get(
                                "S", ""
                            ),
                            "created_at": comment_map.get("created_at", {}).get(
                                "S", ""
                            ),
                        }
                    )
        else:
            self.ticket["ticket_comments"] = []

        self.on_save = on_save
        self.on_cancel = on_cancel
        self.style_manager = StyleManager()
        self.cognito_middleware = CognitoMiddleware()
        self.dynamo_middleware = DynamoMiddleware(config.aws_tickets_table_name)
        self.new_comment = ""
        self._config()

    def _config(self):
        self.style_manager.set_styles(
            {
                "ticket_view": {
                    "container": """
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: 2rem;
                    background-color: transparent;
                    border-radius: 0.75rem;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    """,
                    "comments_container": """
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                    """,
                    "comments_list": """
                    flex-grow: 1;
                    overflow-y: auto;
                    padding: 1rem;
                    background-color: #ffffff;
                    border-radius: 0.5rem;
                    margin-bottom: 1rem;
                    """,
                    "comment_input": """
                    display: flex;
                    gap: 0.5rem;
                    padding: 0.75rem;
                    background-color: #ffffff;
                    border-radius: 0.5rem;
                    border: 1px solid #e0e0e0;
                    """,
                    "button": """
                    background-color: #007bff;
                    color: #ffffff;
                    border-radius: 0.5rem;
                    padding: 0.5rem 1rem;
                    font-weight: bold;
                    """,
                    "input": """
                    border: 1px solid #e0e0e0;
                    border-radius: 0.5rem;
                    padding: 0.5rem;
                    width: 100%;
                    """,
                    "comment": """
                    min-width: 33%;
                    """,
                }
            }
        )

    def _add_comment(self):
        if not self.new_comment.strip():
            return

        try:
            user_id = self.cognito_middleware.get_user_id()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            comment = {
                "comment_id": {"S": str(len(self.ticket.get("ticket_comments", [])))},
                "user_id": {"S": user_id},
                "comment_text": {"S": self.new_comment},
                "created_at": {"S": current_time},
            }

            key = {
                "ticket_id": {"S": self.ticket["ticket_id"]},
                "user_id": {"S": self.ticket["user_id"]},
            }

            if "ticket_comments" not in self.ticket:
                self.ticket["ticket_comments"] = []

            update_expr = "SET ticket_comments = list_append(if_not_exists(ticket_comments, :empty_list), :new_comment)"
            expr_values = {
                ":new_comment": {"L": [{"M": comment}]},
                ":empty_list": {"L": []},
            }

            self.dynamo_middleware.update_item(key, update_expr, expr_values)
            self.ticket["ticket_comments"].append(
                {
                    "comment_id": str(len(self.ticket.get("ticket_comments", []))),
                    "user_id": user_id,
                    "comment_text": self.new_comment,
                    "created_at": current_time,
                }
            )

            self.new_comment = ""
            self.render_comments.refresh()
            ui.notify("Comment added successfully", type="positive")

            # Scroll to bottom after adding comment
            self.scroll_area.scroll_to(percent=1.0)

        except Exception as e:
            print(f"Error adding comment: {str(e)}")
            ui.notify("Error adding comment", type="negative")

    def _handle_save(self):
        if self.on_save:
            self.on_save(self.ticket)

    def _get_user_name(self, user_id):
        try:
            # Get username from user_id
            response = self.cognito_middleware.client.list_users(
                UserPoolId=self.cognito_middleware.user_pool_id,
                Filter=f'sub = "{user_id}"',
            )

            if response["Users"]:
                user = response["Users"][0]
                attributes = {
                    attr["Name"]: attr["Value"] for attr in user["Attributes"]
                }
                given_name = attributes.get("given_name", "")
                family_name = attributes.get("family_name", "")
                if given_name and family_name:
                    return f"{given_name} {family_name[0]}"
                return user_id
            return user_id
        except Exception as e:
            print(f"Error getting user name: {str(e)}")
            return user_id

    @ui.refreshable
    def render_comments(self):
        ui.query(".q-page").classes("flex flex-col")
        ui.query(".nicegui-content").classes("w-full flex-grow")
        ui.query(".q-message-container > div").classes("w-2/3")

        with ui.column().classes("w-full max-w-3xl mx-auto flex-grow"):
            self.scroll_area = (
                ui.scroll_area()
                .classes("w-full flex-grow")
                .style("border: 1px solid #e0e0e0; border-radius: 0.5rem;")
            )

            with self.scroll_area:
                self.message_container = ui.column().classes("w-full p-4")
                with self.message_container:
                    comments = self.ticket.get("ticket_comments", [])

                    # Only sort if we have comments with created_at
                    if comments and all(
                        "created_at" in comment for comment in comments
                    ):
                        comments = sorted(
                            comments,
                            key=lambda x: datetime.strptime(
                                x["created_at"].split(".")[0], "%Y-%m-%d %H:%M:%S"
                            ),
                        )

                    if not comments:
                        ui.chat_message(
                            text="No comments yet. Start the conversation!",
                            name="System",
                            sent=False,
                        )

                    current_date = None
                    for comment in comments:
                        if "created_at" in comment and "comment_text" in comment:
                            created_at = datetime.strptime(
                                comment["created_at"].split(".")[0], "%Y-%m-%d %H:%M:%S"
                            )

                            # Check if we need to add a date separator
                            comment_date = created_at.date()
                            if current_date != comment_date:
                                current_date = comment_date
                                with ui.row().classes("w-full justify-center my-4"):
                                    ui.label(
                                        current_date.strftime("%A, %B %d, %Y")
                                    ).classes("text-gray-500")

                            time_str = created_at.strftime("%I:%M %p")

                            is_current_user = (
                                comment["user_id"]
                                == self.cognito_middleware.get_user_id()
                            )

                            user_name = self._get_user_name(comment["user_id"])

                            with ui.row().classes("w-full"):
                                if is_current_user:
                                    ui.label().classes("flex-grow")
                                ui.chat_message(
                                    text=f"{comment['comment_text']}\n\n{time_str}",
                                    name=user_name,
                                    sent=is_current_user,
                                ).classes("w-full")
                                if not is_current_user:
                                    ui.label().classes("flex-grow")

            # Scroll to bottom after rendering
            self.scroll_area.scroll_to(percent=1.0)

            with ui.row().classes("w-full my-2"):
                with ui.column().classes("flex flex-1"):
                    text_input = (
                        ui.input(placeholder="Add a comment...")
                        .props("outlined rounded")
                        .classes("w-full")
                    ).bind_value(self, "new_comment")
                    text_input.on("keydown.enter", self._add_comment)
                with ui.column().classes("flex items-center justify-center").style(
                    "height:100%"
                ):
                    ui.button(
                        icon="send",
                        on_click=self._add_comment,
                    ).props("dense round")

    def render(self):
        with ui.card().style(
            self.style_manager.get_style("ticket_view.container")
        ).classes("w-full"):
            with ui.card().style("width:80%; height:70%;"):
                with ui.row().classes("w-full justify-between gap-2 mb-4"):
                    with ui.row().classes(
                        "flex-1 items-center justify-between gap-2 max-w-[60%]"
                    ):
                        ui.input(
                            "Title", value=self.ticket.get("ticket_title", "")
                        ).bind_value_to(self.ticket, "ticket_title").classes(
                            "w-3/5"
                        ).props(
                            "outlined"
                        )
                        with ui.input("Due Date").props("outlined") as date:
                            with ui.menu().props("no-parent-event") as menu:
                                with ui.date().bind_value(date).bind_value_to(
                                    self.ticket, "ticket_due_date"
                                ):
                                    with ui.row().classes("justify-end"):
                                        ui.button("Close", on_click=menu.close).props(
                                            "flat"
                                        )
                                with date.add_slot("append"):
                                    ui.icon("edit_calendar").on(
                                        "click", menu.open
                                    ).classes("cursor-pointer")

                    with ui.row().classes("gap-2"):
                        ui.button("X", color="red", on_click=self.on_cancel).props(
                            "round outline"
                        )

                with ui.grid(columns=5).classes("w-full h-full gap-4"):
                    with ui.column().classes("col-span-3"):
                        ui.textarea(
                            "Description",
                            value=self.ticket.get("ticket_description", ""),
                        ).style(
                            self.style_manager.get_style("ticket_view.input")
                        ).bind_value_to(
                            self.ticket, "ticket_description"
                        )
                        with ui.row().classes("w-full gap-4"):
                            ui.select(
                                {1: "Low", 2: "Medium", 3: "High"},
                                value=self.ticket.get("ticket_priority", 1),
                                label="Priority",
                            ).style(
                                self.style_manager.get_style("ticket_view.input")
                            ).bind_value_to(
                                self.ticket, "ticket_priority"
                            )
                            ui.select(
                                ["Pending", "In Progress", "Completed"],
                                value=self.ticket.get("ticket_status", "Pending"),
                                label="Status",
                            ).style(
                                self.style_manager.get_style("ticket_view.input")
                            ).bind_value_to(
                                self.ticket, "ticket_status"
                            )
                        with ui.row().classes("w-full h-full items-end"):
                            ui.button("Update", on_click=self._handle_save).style(
                                self.style_manager.get_style("ticket_view.button")
                            )

                    with ui.column().classes("col-span-2"):
                        self.render_comments()
