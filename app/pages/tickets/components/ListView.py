from nicegui import ui
from modules import StyleManager
from middleware.dynamo import DynamoMiddleware
from middleware.cognito import CognitoMiddleware
from config import config
from utils.func.util_functions import truncate_text, get_ordinal_suffix
from datetime import datetime
from .TicketView import TicketViewComponent


def format_priority(priority: int) -> str:
    priority_map = {1: "Low", 2: "Medium", 3: "High"}
    return priority_map.get(priority, "Unknown")


def format_date(date_str: str) -> str:
    try:
        if isinstance(date_str, datetime):
            date_obj = date_str
        else:
            date_obj = datetime.strptime(date_str.split(".")[0], "%Y-%m-%d %H:%M:%S")

        day = date_obj.day
        suffix = get_ordinal_suffix(day)
        return date_obj.strftime(f"%A, %B {day}{suffix}")
    except (ValueError, AttributeError):
        return date_str


class ListViewComponent:
    def __init__(self, state, on_click_select_ticket):
        self.state = state
        self.on_click_select_ticket = on_click_select_ticket
        self.style_manager = StyleManager()
        self.dynamo_middleware = DynamoMiddleware(config.aws_tickets_table_name)
        self._config()

    def _config(self):
        self.style_manager.set_styles(
            {
                "list_view": {
                    "card": """
                    width: 100%;
                    height: calc(100vh - 200px);
                    padding: 1rem;
                    background-color: #f8fafc;
                    """
                }
            }
        )

    def _format_grid_data(self, tickets):
        return [
            {
                "title": ticket["ticket_title"],
                "description": truncate_text(ticket["ticket_description"], 50),
                "due_date": format_date(ticket["ticket_due_date"]),
                "status": ticket["ticket_status"],
                "priority": format_priority(int(ticket["ticket_priority"])),
                "raw_data": ticket,
            }
            for ticket in tickets
        ]

    def _on_row_clicked(self, e):
        ticket_data = e.args["data"]["raw_data"]
        dialog = ui.dialog().props("maximized persistent")
        with dialog:
            TicketViewComponent(
                ticket_data=ticket_data,
                on_save=lambda t: self._save_ticket(t, dialog),
                on_cancel=dialog.close,
            ).render()
        dialog.open()

    def _save_ticket(self, ticket_data, dialog):
        try:
            self.dynamo_middleware.put_item(ticket_data)
            ui.notify("Ticket updated successfully", type="positive")
            self.on_click_select_ticket(ticket_data)
            dialog.close()
            self.render_content.refresh()
        except Exception as e:
            print(f"Error updating ticket: {str(e)}")
            ui.notify("Error updating ticket", type="negative")

    @ui.refreshable
    def render_content(self):
        tickets = self.state["tickets"]
        grid_data = self._format_grid_data(tickets)

        grid = ui.aggrid(
            {
                "columnDefs": [
                    {"headerName": "Title", "field": "title", "flex": 2},
                    {
                        "headerName": "Description",
                        "field": "description",
                        "flex": 3,
                    },
                    {"headerName": "Due Date", "field": "due_date", "flex": 2},
                    {"headerName": "Status", "field": "status", "flex": 1},
                    {"headerName": "Priority", "field": "priority", "flex": 1},
                ],
                "rowData": grid_data,
                "defaultColDef": {
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                },
                "rowSelection": "single",
                "theme": "material",
            }
        ).classes("h-[70vh]")

        grid.on("cellClicked", self._on_row_clicked)

    def render(self):
        with ui.card().style(self.style_manager.get_style("list_view.card")):
            self.render_content()
