from nicegui import ui
from config import config
from components.shared import StaticPage
from utils.helpers import dynamo_adapter
from models import ManagedState, TicketRecord
from uuid import uuid4
from datetime import datetime
import asyncio


class TicketsPage(StaticPage):
    def __init__(self, storage_manager):
        super().__init__(
            page_title="Tickets",
            page_route="/tickets",
            page_description="Tickets",
            storage_manager=storage_manager,
        )
        self.dynamo_adapter = dynamo_adapter(config.aws_tickets_table_name)
        self.settings_adapter = dynamo_adapter(config.aws_settings_table_name)
        self.state = ManagedState("tickets")
        self.current_view = "ticket_table_view"  # Default view
        self._load_ticket_schema()
        self._onload()

    def _load_ticket_schema(self):
        """Load ticket schema from settings table"""
        key = {"uuid": {"S": "ticket_system"}, "tag": {"S": "ticket_system_schema"}}
        schema_data = self.settings_adapter.get_item(key)

        if schema_data and "schemas" in schema_data:
            self.state.set("ticket_schema", schema_data["schemas"])
        else:
            self.state.set("ticket_schema", [])

    def _get_categories(self):
        """Get list of ticket categories from schema"""
        schemas = self.state.get("ticket_schema", [])
        return {schema["category"]: schema["category"] for schema in schemas}

    def _get_subcategories(self, category):
        """Get subcategories for selected category"""
        schemas = self.state.get("ticket_schema", [])
        for schema in schemas:
            if schema["category"] == category:
                return {
                    sub["subcategory"]: sub["subcategory"]
                    for sub in schema.get("subcategories", [])
                }
        return {}

    def _get_status_options(self, category):
        """Get status options for selected category"""
        schemas = self.state.get("ticket_schema", [])
        for schema in schemas:
            if schema["category"] == category:
                return {
                    status["status"]: status["status"]
                    for status in schema.get("status_options", [])
                }
        return {}

    def _onload(self):
        self.state.set("tickets", self.get_tickets())
        self.state.set("view", "create_ticket")

    def get_tickets(self):
        """Load all ticket records

        Returns:
            list: List of ticket records
        """
        response = self.dynamo_adapter.scan()

        formatted_records = []
        for item in response:
            formatted_record = {
                "ticket_id": item.get("ticket_id", {}).get("S", ""),
                "user_id": item.get("user_id", {}).get("S", ""),
                "category": item.get("category", {}).get("S", ""),
                "subcategory": item.get("subcategory", {}).get("S", ""),
                "status": item.get("status", {}).get("S", ""),
                "created_at": item.get("created_at", {}).get("S", ""),
                "description": item.get("description", {}).get("S", ""),
                "assigned_to": item.get("assigned_to", {}).get("S", ""),
            }
            formatted_records.append(formatted_record)

        return formatted_records

    @classmethod
    def format_records(cls, records: list["TicketRecord"]) -> list[dict]:
        """Convert a list of TicketRecords to list of simplified dictionaries."""
        return [record.to_dict() for record in records]

    def ticket_table_view(self):
        """Render the tickets table view"""
        with ui.card().classes("w-full"):
            # Toolbar
            with ui.row().classes("w-full items-center q-pa-md"):
                ui.label("Tickets").classes("text-h6")
                ui.space()
                ui.button(
                    "New Ticket",
                    on_click=lambda: self._change_view("create_ticket_view"),
                    color=self.theme_manager.get_color("button-basic"),
                ).classes("q-ml-md")

            # Table
            tickets = self.state.get("tickets", [])
            column_defs = [
                {"field": "assigned_to", "headerName": "Assigned To", "width": 150},
                {"field": "status", "headerName": "Status", "width": 120},
                {"field": "category", "headerName": "Category", "width": 150},
                {"field": "subcategory", "headerName": "Subcategory", "width": 150},
                {"field": "description", "headerName": "Description", "width": 400},
                {"field": "created_at", "headerName": "Created At", "width": 180},
                {"field": "ticket_id", "headerName": "Ticket ID", "hide": True},
            ]

            ui.aggrid(
                {
                    "columnDefs": column_defs,
                    "rowData": tickets,
                    "defaultColDef": {
                        "sortable": True,
                        "filter": True,
                        "resizable": True,
                    },
                    "pagination": True,
                    "paginationAutoPageSize": True,
                }
            ).classes("w-full min-h-[70vh]")

    @ui.refreshable
    def render_subcategory_dropdown(self):
        """Render subcategory dropdown with options based on selected category"""
        category = self.state.get("category")
        subcategories = self._get_subcategories(category) if category else {}

        ui.select(
            options=subcategories,
            value=self.state.get("subcategory"),
            on_change=lambda e: self.state.set("subcategory", e.value),
        ).classes("w-full")

    def create_ticket_view(self):
        """Render the create ticket form with an improved professional layout."""
        with ui.card().classes("w-full transition-opacity duration-300"):
            # Header with back button and title
            with ui.row().classes("w-full items-center border-b border-gray-200 p-4"):
                ui.button(
                    icon="arrow_back",
                    on_click=lambda: self._change_view("ticket_table_view"),
                    color=self.theme_manager.get_color("button-basic"),
                ).classes("q-mr-md")
                ui.label("Create Ticket").classes("text-h6")

            # Form content
            with ui.column().classes("w-full p-4 gap-6"):
                # Category and Subcategory in a row
                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("Category").classes("text-subtitle1 q-mb-sm")
                        ui.select(
                            options=self._get_categories(),
                            value=self.state.get("category"),
                            on_change=lambda e: self._on_category_change(e.value),
                        ).classes("w-full")

                    with ui.column().classes("flex-1"):
                        ui.label("Subcategory").classes("text-subtitle1 q-mb-sm")
                        self.render_subcategory_dropdown()

                # Description section
                with ui.column().classes("w-full"):
                    ui.label("Description").classes("text-subtitle1 q-mb-sm")
                    ui.editor(
                        placeholder="Please provide a detailed description of your issue...",
                        on_change=lambda e: self.state.set("description", e.value),
                    ).classes("w-full h-[400px]")

                # Action buttons in a row at the bottom
                with ui.row().classes(
                    "w-full justify-end gap-4 pt-4 border-t border-gray-200"
                ):
                    ui.button(
                        "Cancel",
                        on_click=lambda: self._change_view("ticket_table_view"),
                        color=self.theme_manager.get_color("button-basic"),
                    ).props("flat").style(
                        f"color: {self.theme_manager.get_color('button-basic', 'text')};"
                    )

                    ui.button(
                        "Create Ticket",
                        on_click=self.create_ticket,
                        color=self.theme_manager.get_color("button-basic"),
                    ).props("unelevated").style(
                        f"color: {self.theme_manager.get_color('button-basic', 'text')};"
                    )

    def _change_view(self, new_view):
        """Change the current view and refresh the display"""
        self.current_view = new_view
        self.process_rendering.refresh()

    @ui.refreshable
    def process_rendering(self):
        """Process and render the current view"""
        if self.current_view == "ticket_table_view":
            self.ticket_table_view()
        elif self.current_view == "create_ticket_view":
            self.create_ticket_view()

    def _on_category_change(self, category):
        """Handle category selection change"""
        self.state.set("category", category)
        self.state.set("subcategory", None)  # Reset subcategory selection
        self.render_subcategory_dropdown.refresh()

    def create_ticket(self):
        """Handle ticket creation with schema validation"""
        category = self.state.get("category")
        subcategory = self.state.get("subcategory")
        description = self.state.get("description")

        if not all([category, subcategory, description]):
            ui.notify("Please fill in all required fields", type="negative")
            return

        status_options = self._get_status_options(category)
        initial_status = next(iter(status_options.values()), "open")

        # Get user ID using the correct method
        user_id = self.storage_manager.get_user_id()
        if not user_id:
            ui.notify("User ID not found. Please log in again.", type="negative")
            return

        # Create ticket with new schema
        ticket = {
            "ticket_id": {"S": str(uuid4())},
            "user_id": {"S": user_id},  # Using get_user_id() method
            "category": {"S": category},
            "subcategory": {"S": subcategory},
            "status": {"S": initial_status},
            "created_at": {"S": datetime.utcnow().isoformat()},
            "description": {"S": description},
            "assigned_to": {"S": "unassigned"},  # Default value
        }

        try:
            self.dynamo_adapter.put_item(ticket)
            self._onload()
            self._change_view("ticket_table_view")
            ui.notify("Ticket created successfully", type="positive")
        except Exception as e:
            ui.notify(f"Error creating ticket: {str(e)}", type="negative")

    def content(self):
        """Main content renderer"""
        with ui.column().classes("w-full h-[80vh]"):
            self.process_rendering()


def tickets_page(storage_manager):
    page = TicketsPage(storage_manager)
    page.render()
