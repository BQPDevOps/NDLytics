from nicegui import ui
from modules import StyleManager
from models import TicketModel
from middleware.dynamo import DynamoMiddleware
from middleware.cognito import CognitoMiddleware
import uuid
from config import config
from datetime import datetime
from utils.helpers import *
from utils.func import *
from contextlib import contextmanager
import asyncio


def format_priority(priority: int) -> str:
    priority_map = {1: "Low", 2: "Medium", 3: "High"}
    return priority_map.get(priority, "Unknown")


class NewTicketInput:
    def __init__(self):
        self.ticket_title: str = ""
        self.description: str = ""
        self.priority: int = 1
        self.due_date: str = ""
        self.status: str = "pending"

    @property
    def is_valid(self):
        return bool(self.ticket_title.strip() and self.description.strip())


class TicketsComponent:
    def __init__(self):
        self.style_manager = StyleManager()
        self.cognito_middleware = CognitoMiddleware()
        self.dynamo_middleware = DynamoMiddleware(config.aws_tickets_table_name)
        self.new_ticket_input = NewTicketInput()
        self.dialog = None
        self._config()

    def _config(self):
        self.style_manager.set_styles(
            {
                "tickets_component": {
                    "title_container": """
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    padding-left:1rem;
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

    @contextmanager
    def _dialog_manager(self):
        try:
            self.dialog = ui.dialog().props("medium")
            yield self.dialog
        finally:
            if self.dialog and self.dialog.value:
                self.dialog.close()
            self.dialog = None

    def _add_ticket(self, dialog):
        try:
            if not self.new_ticket_input.is_valid:
                ui.notify("Title and description are required", type="warning")
                return

            user_id = self.cognito_middleware.get_user_id()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

            due_date = self.new_ticket_input.due_date
            if not due_date:
                due_date = current_time
            elif isinstance(due_date, datetime):
                due_date = due_date.strftime("%Y-%m-%d %H:%M:%S.%f")

            ticket = TicketModel(
                ticket_id=str(uuid.uuid4()),
                user_id=user_id,
                ticket_title=self.new_ticket_input.ticket_title,
                ticket_description=self.new_ticket_input.description,
                ticket_priority=self.new_ticket_input.priority,
                ticket_due_date=due_date,
                ticket_status=self.new_ticket_input.status,
                ticket_create_on=current_time,
                ticket_created_by=user_id,
                ticket_updated_on=current_time,
                ticket_updated_by=user_id,
                ticket_assigned_to=[user_id],
                ticket_comments=[],
            )

            item = {
                "ticket_id": {"S": str(ticket.ticket_id)},
                "user_id": {"S": str(ticket.user_id)},
                "ticket_title": {"S": str(ticket.ticket_title)},
                "ticket_description": {"S": str(ticket.ticket_description)},
                "ticket_priority": {"N": str(ticket.ticket_priority)},
                "ticket_due_date": {"S": str(ticket.ticket_due_date)},
                "ticket_status": {"S": str(ticket.ticket_status)},
                "ticket_create_on": {"S": str(ticket.ticket_create_on)},
                "ticket_created_by": {"S": str(ticket.ticket_created_by)},
                "ticket_updated_on": {"S": str(ticket.ticket_updated_on)},
                "ticket_updated_by": {"S": str(ticket.ticket_updated_by)},
                "ticket_assigned_to": {
                    "L": [{"S": str(user)} for user in ticket.ticket_assigned_to]
                },
                "ticket_comments": {"L": []},
            }

            self.dynamo_middleware.put_item(item)
            dialog.close()
            ui.notify("Ticket added successfully", type="positive")
            self.render_tickets_list.refresh()
        except Exception as e:
            print(f"Error adding ticket: {str(e)}")
            ui.notify("Error adding ticket", type="negative")
        finally:
            self.new_ticket_input = NewTicketInput()

    def _reset_and_close(self):
        self.new_ticket_input = NewTicketInput()
        if self.dialog:
            self.dialog.close()

    def open_ticket_modal(self):
        with ui.dialog().props("medium") as dialog:
            with ui.card().classes("w-full"):
                with ui.row().classes("w-full"):
                    ui.label("Add New Ticket").style(
                        "font-size:1.2rem;font-weight:bold;color:#4A4A4A;"
                    )
                with ui.column().style(
                    self.style_manager.get_style(
                        "tickets_component.add_task_modal_header_container"
                    )
                ):
                    ui.input(
                        placeholder="Ticket title",
                        value=self.new_ticket_input.ticket_title,
                    ).props("outlined dense").classes("w-full").bind_value_to(
                        self.new_ticket_input, "ticket_title"
                    )
                    with ui.row().classes("w-full flex justify-end flex-row"):
                        with ui.column().classes("flex-grow"):
                            ui.select(
                                {1: "Low", 2: "Medium", 3: "High"},
                                value=self.new_ticket_input.priority,
                            ).props("outlined dense").classes("w-full").bind_value_to(
                                self.new_ticket_input, "priority"
                            )
                        with ui.column():
                            with ui.input("Date").props("outlined dense") as date:
                                with ui.menu().props("no-parent-event") as menu:
                                    with ui.date().bind_value(date).bind_value_to(
                                        self.new_ticket_input, "due_date"
                                    ):
                                        with ui.row().classes("justify-end"):
                                            ui.button(
                                                "Close", on_click=menu.close
                                            ).props("flat")
                                    with date.add_slot("append"):
                                        ui.icon("edit_calendar").on(
                                            "click", menu.open
                                        ).classes("cursor-pointer")
                with ui.column().style(
                    self.style_manager.get_style(
                        "tickets_component.add_task_modal_input_container"
                    )
                ):
                    ui.editor(
                        placeholder="Ticket description",
                        value=self.new_ticket_input.description,
                    ).style("height:100%;width:100%;").bind_value_to(
                        self.new_ticket_input, "description"
                    )
                with ui.row().classes("w-full flex justify-end flex-row"):
                    ui.button("Cancel", on_click=dialog.close).props("flat")
                    ui.button("Add", on_click=lambda: self._add_ticket(dialog)).props(
                        "flat"
                    )
            dialog.open()

    def _get_tickets(self):
        user_id = self.cognito_middleware.get_user_id()
        expression_values = {":uid": {"S": user_id}, ":status": {"S": "pending"}}
        response = self.dynamo_middleware.scan(
            filter_expression="user_id = :uid AND ticket_status = :status",
            expression_attribute_values=expression_values,
        )
        return response["Items"] if "Items" in response else []

    def parse_date(self, date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    def _render_ticket_item(self, ticket):
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

        async def complete_ticket(ticket_info):
            # Animate item off screen
            item_container.style(add="transform: translateX(-100%);")
            await asyncio.sleep(0.3)  # Wait for animation

            # Update ticket in DynamoDB
            try:
                self.dynamo_middleware.update_item(
                    key={
                        "ticket_id": {"S": ticket_info["ticket_id"]},
                        "user_id": {"S": ticket_info["user_id"]},
                    },
                    update_expression="SET ticket_status = :status",
                    expression_attribute_values={":status": {"S": "Completed"}},
                )
                await ui.run_javascript("window.location.reload()")
            except Exception as e:
                print(f"Error updating ticket: {str(e)}")
                ui.notify("Error updating ticket status", type="negative")

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
                    await complete_ticket(ticket)
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
                    value=ticket["ticket_status"] == "Completed",
                    on_change=on_check_change,
                )
                with ui.item_section().classes("flex-grow gap-0 relative"):
                    ui.button("undo", on_click=handle_undo).props("flat").classes(
                        "absolute right-[-8rem] top-1/2 -translate-y-1/2"
                    )
                    with ui.row().classes("w-full justify-between"):
                        ui.label(truncate_text(ticket["ticket_title"], 15)).style(
                            "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                        )
                        ui.label(
                            self.parse_date(ticket["ticket_due_date"]).strftime(
                                "%m-%d-%Y"
                            )
                        ).style("font-size:1rem;color:#4A4A4A;padding-right:0.2rem")
                    with ui.row().classes("w-full flex-grow justify-end"):
                        with ui.row():
                            status = ticket["ticket_status"].lower()
                            color = {
                                "completed": "green",
                                "pending": "orange",
                                "overdue": "red",
                            }.get(status, "grey")
                            ui.chip(
                                ticket["ticket_status"],
                                color=color,
                                text_color="white",
                            ).classes("text-md").props("dense")

    @ui.refreshable
    def render_tickets_list(self):
        try:
            tickets = self._get_tickets()
            formatted_tickets = [dynamo_to_json(ticket) for ticket in tickets]

            # Sort tickets by due date
            sorted_tickets = sorted(
                formatted_tickets, key=lambda x: self.parse_date(x["ticket_due_date"])
            )

            with ui.column().classes("w-full flex flex-col"):
                if sorted_tickets:
                    with ui.column().classes("w-full"):
                        with ui.scroll_area().classes("w-full max-h-[600px]"):
                            for ticket in sorted_tickets:
                                self._render_ticket_item(ticket)
                else:
                    with ui.column().classes("w-full p-4 text-center"):
                        ui.label("No tickets available").style(
                            "color: #666; font-style: italic;"
                        )
        except Exception as e:
            print(f"Error rendering tickets list: {str(e)}")
            with ui.column().classes("w-full p-4 text-center"):
                ui.label("Unable to load tickets").style(
                    "color: #666; font-style: italic;"
                )

    def render(self):
        with ui.card().classes("w-full"):
            with ui.row().style(
                self.style_manager.get_style("tickets_component.title_container")
            ):
                ui.label("Tickets").style(
                    self.style_manager.get_style("tickets_component.title_text")
                )
                ui.button(icon="add", on_click=self.open_ticket_modal).props(
                    "round size=sm"
                ).style("margin-right:0.6rem;")
            self.render_tickets_list()


def format_priority(priority: int) -> str:
    priority_map = {1: "Low", 2: "Moderate", 3: "High"}
    return priority_map.get(priority, "Unknown")


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
