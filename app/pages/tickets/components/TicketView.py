from nicegui import ui
from datetime import datetime
from modules import StyleManager
from middleware.dynamo import DynamoMiddleware
from middleware.cognito import CognitoMiddleware
from config import config
import asyncio


class TicketViewComponent:
    def __init__(self, ticket_data, on_save=None, on_cancel=None):
        self.ticket = ticket_data.copy()  # Create a copy to track changes
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
                    padding: 2rem;
                    background-color: #f0f4f8;
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
                    width: 100%;
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
                }
            }
        )

    async def _send_comment(self, text_input):
        if not text_input.value.strip():
            return

        comment_text = text_input.value
        text_input.value = ""

        user_id = self.cognito_middleware.get_user_id()
        comment = {
            "comment_id": str(len(self.ticket.get("ticket_comments", []))),
            "user_id": user_id,
            "comment_text": comment_text,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
        }

        if "ticket_comments" not in self.ticket:
            self.ticket["ticket_comments"] = []

        self.ticket["ticket_comments"].append(comment)
        self.render_comments.refresh()

    def _handle_save(self):
        if self.on_save:
            self.on_save(self.ticket)

    @ui.refreshable
    def render_comments(self):
        with ui.card().style(
            self.style_manager.get_style("ticket_view.comments_container")
        ).classes("w-full"):
            with ui.scroll_area().style(
                self.style_manager.get_style("ticket_view.comments_list")
            ):
                for comment in self.ticket.get("ticket_comments", []):
                    with ui.chat_message(
                        text=comment["comment_text"], name="User", sent=True
                    ):
                        ui.label(comment["created_at"]).classes("text-xs text-gray-500")

            with ui.row().style(
                self.style_manager.get_style("ticket_view.comment_input")
            ):
                text_input = ui.input(placeholder="Add a comment...").style(
                    self.style_manager.get_style("ticket_view.input")
                )
                text_input.on(
                    "keydown.enter",
                    lambda: asyncio.create_task(self._send_comment(text_input)),
                )
                ui.button(
                    icon="send",
                    on_click=lambda: asyncio.create_task(
                        self._send_comment(text_input)
                    ),
                ).style(self.style_manager.get_style("ticket_view.button"))

    def render(self):
        with ui.card().classes("w-full").style(
            "background-color: transparent;display: flex; justify-content:center;align-items:center;"
        ):
            with ui.card().style("height:70%;width:80%;").classes("rounded-lg"):
                with ui.row().classes("w-full align-center gap-2 mb-4"):
                    with ui.row().classes("flex-1"):
                        ui.input(
                            "Title", value=self.ticket.get("ticket_title", "")
                        ).bind_value_to(self.ticket, "ticket_title")

                    with ui.row().classes("gap-2 h-full align-center"):
                        ui.button("Cancel", on_click=self.on_cancel).style(
                            self.style_manager.get_style("ticket_view.button")
                        )
                        ui.button("Save", on_click=self._handle_save).style(
                            self.style_manager.get_style("ticket_view.button")
                        )

                with ui.grid(columns=5).classes("w-full gap-4"):
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
                                ["pending", "in_progress", "completed"],
                                value=self.ticket.get("ticket_status", "pending"),
                                label="Status",
                            ).style(
                                self.style_manager.get_style("ticket_view.input")
                            ).bind_value_to(
                                self.ticket, "ticket_status"
                            )
                        with ui.input("Due Date").style(
                            self.style_manager.get_style("ticket_view.input")
                        ) as date:
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

                    with ui.column().classes("col-span-2"):
                        self.render_comments()
