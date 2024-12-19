from nicegui import ui
from icecream import ic
from models import TicketModel
from datetime import datetime
from middleware.dynamo import DynamoMiddleware
from config import config


class TicketViewComponent:
    def __init__(self, state):
        self.state = state
        self.ticket = state["selected_ticket"]
        self.dynamo_middleware = DynamoMiddleware(config.aws_tickets_table_name)

    def _update_ticket(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        due_date = self.ticket["ticket_due_date"]
        if isinstance(due_date, datetime):
            due_date = due_date.strftime("%Y-%m-%d %H:%M:%S.%f")

        key = {
            "ticket_id": {"S": self.ticket["ticket_id"]},
            "user_id": {"S": self.ticket["user_id"]},
        }

        update_expr = """SET
            ticket_title = :title,
            ticket_description = :desc,
            ticket_priority = :priority,
            ticket_due_date = :due_date,
            ticket_status = :status,
            ticket_updated_on = :updated_on"""

        expr_values = {
            ":title": {"S": self.ticket["ticket_title"]},
            ":desc": {"S": self.ticket["ticket_description"]},
            ":priority": {"N": str(self.ticket["ticket_priority"])},
            ":due_date": {"S": due_date},
            ":status": {"S": self.ticket["ticket_status"]},
            ":updated_on": {"S": current_time},
        }

        self.dynamo_middleware.update_item(key, update_expr, expr_values)

    def render(self):
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full"):
                ui.label("Update Task").style(
                    "font-size:1.2rem;font-weight:bold;color:#4A4A4A;"
                )

            with ui.column().classes("w-full"):
                ui.input(placeholder="ticket title...").props("outlined dense").classes(
                    "w-full"
                ).bind_value(self.ticket, "ticket_title")

                with ui.row().classes("w-full flex justify-end flex-row"):
                    with ui.column().classes("flex-grow"):
                        ui.select({1: "Low", 2: "Medium", 3: "High"}).props(
                            "outlined dense"
                        ).classes("w-full").bind_value(self.ticket, "ticket_priority")
                    with ui.column():
                        with ui.input("Date").props("outlined dense") as date:
                            with ui.menu().props("no-parent-event") as menu:
                                with ui.date().bind_value(date).bind_value(
                                    self.ticket, "ticket_due_date"
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
                ui.editor(placeholder="ticket description...").style(
                    "height:30rem;width:100%;"
                ).bind_value(self.ticket, "ticket_description")

            with ui.row().classes("w-full flex justify-end flex-row"):
                ui.button("Update", on_click=self._update_ticket).props("flat")
