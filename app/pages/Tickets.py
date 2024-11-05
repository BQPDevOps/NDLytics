from nicegui import ui
from config import config
from components.shared import StaticPage
from utils.helpers import dynamo_adapter
from models import ManagedState, TicketRecord
from uuid import uuid4
from datetime import datetime
import asyncio
from forms import CreateTicketForm


class TicketsPage(StaticPage):
    def __init__(self, storage_manager):
        super().__init__(
            page_title="Tickets",
            page_route="/tickets",
            page_description="Tickets",
            storage_manager=storage_manager,
        )
        self.dynamo_adapter = dynamo_adapter(config.aws_general_table_name)
        self.state = ManagedState("tickets")
        self.fade_duration = 0.3  # Duration of fade animation in seconds

        self._onload()

    def _onload(self):
        self.state.set("tickets", self.get_tickets())
        self.state.set("view", "create_ticket")

    def get_tickets(self):
        """Load all records with uuid = 'ticket_system'

        Returns:
            list: List of formatted ticket records containing ticket system data
        """
        response = self.dynamo_adapter.scan(
            FilterExpression="#uuid = :uuid_value",
            ExpressionAttributeNames={"#uuid": "uuid"},
            ExpressionAttributeValues={":uuid_value": {"S": "ticket_system"}},
        )

        # Format the items and convert to TicketRecord objects
        formatted_records = []
        for item in response:
            formatted_item = {
                "primary_key": uuid4(),
                "uuid": item.get("uuid", {}).get("S", ""),
                "tag": item.get("tag", {}).get("S", ""),
                "created_at": datetime.fromisoformat(
                    item.get("created_at", {}).get("S", datetime.utcnow().isoformat())
                ),
                "updated_at": datetime.fromisoformat(
                    item.get("updated_at", {}).get("S", datetime.utcnow().isoformat())
                ),
                "attributes": {},
            }

            # Extract attributes without data_type
            if "attributes" in item and "M" in item["attributes"]:
                attrs = item["attributes"]["M"]
                for key, value in attrs.items():
                    if "M" in value and "value" in value["M"]:
                        val = value["M"]["value"]
                        actual_value = next(iter(val.values()))
                        formatted_item["attributes"][key] = {"value": actual_value}

            record = TicketRecord(**formatted_item)
            formatted_records.append(record.to_dict())

        return formatted_records

    @classmethod
    def format_records(cls, records: list["TicketRecord"]) -> list[dict]:
        """Convert a list of TicketRecords to list of simplified dictionaries."""
        return [record.to_dict() for record in records]

    @ui.refreshable
    def render_tickets_table(self):
        """Display tickets data in an ag-grid table."""
        with ui.card().classes(
            "w-full h-[100%] transition-opacity duration-300"
        ) as card:
            self.tickets_container = card
            ui.label("Tickets").classes("text-h6 q-mb-md")

            # Get the tickets data
            tickets = self.state.get("tickets")
            print(tickets)
            # Define the column definitions for the grid
            column_defs = [
                {"field": "uuid", "headerName": "UUID"},
                {"field": "ticket_id", "headerName": "Ticket ID"},
                {"field": "status", "headerName": "Status"},
                {"field": "created_at", "headerName": "Created At"},
                {"field": "updated_at", "headerName": "Updated At"},
                {"field": "description", "headerName": "Description"},
                # Add more columns as needed based on your ticket data structure
            ]
            with ui.row().classes("w-full"):
                ui.space()
                ui.button(
                    "Create Ticket",
                    on_click=self.on_click_create_ticket,
                    color=self.theme_manager.get_color("button-basic"),
                ).style(
                    f"color: {self.theme_manager.get_color('button-basic', 'text')};"
                )
            with ui.column().classes("w-full"):
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
                ).classes("w-full min-h-[62vh]")

    def render_create_ticket(self):
        """Render the create ticket form with a grid layout."""
        with ui.card().classes("w-full transition-opacity duration-300") as card:
            self.create_ticket_container = card
            CreateTicketForm().render()
            # with ui.column().classes("w-full h-[80vh] gap-4"):
            #     # Header
            #     ui.label("Create Ticket").classes("text-h6 q-mb-md")

            #     # Top row with issue type selector
            #     with ui.row().classes("w-full gap-4"):
            #         ui.select(
            #             label="Issue Type",
            #             options={
            #                 "account": "Account Issue",
            #                 "payment": "Payment Issue",
            #                 "dialer": "Dialer Issue",
            #                 "general": "General Issue",
            #             },
            #             value="general",
            #             on_change=lambda e: self.state.set("issue_type", e.value),
            #         ).classes("w-full")

            #     # Main content grid
            #     with ui.grid().classes("w-full h-[100%] gap-4").style(
            #         "grid-template-columns: 3fr 1fr;"
            #     ):
            #         # Left column - Description
            #         with ui.column().classes("gap-2"):
            #             ui.textarea(
            #                 label="Description",
            #                 placeholder="Enter ticket description...",
            #                 on_change=lambda e: self.state.set("description", e.value),
            #             ).classes("w-full h-[300px]")

            #         # Right column - Priority
            #         with ui.column().classes("gap-2"):
            #             ui.select(
            #                 label="Priority",
            #                 options={"low": "Low", "medium": "Medium", "high": "High"},
            #                 value="low",
            #                 on_change=lambda e: self.state.set("priority", e.value),
            #             ).classes("w-full")

            #     # Bottom row with actions
            #     with ui.row().classes("w-full gap-4 justify-end"):
            #         ui.button(
            #             "Cancel",
            #             on_click=lambda: asyncio.create_task(
            #                 self.transition_view("view_all")
            #             ),
            #             color=self.theme_manager.get_color("button-basic"),
            #         ).style(
            #             f"color: {self.theme_manager.get_color('button-basic', 'text')};"
            #         )

            #         ui.button(
            #             "Create",
            #             on_click=self.create_ticket,
            #             color=self.theme_manager.get_color("button-basic"),
            #         ).style(
            #             f"color: {self.theme_manager.get_color('button-basic', 'text')};"
            #         )

    def create_ticket(self):
        """Handle ticket creation."""
        # Get form values from state
        issue_type = self.state.get("issue_type")
        description = self.state.get("description")
        priority = self.state.get("priority")

        # Create ticket record
        ticket = {
            "uuid": "ticket_system",
            "tag": f"ticket_{uuid4()}",  # Unique identifier for the ticket
            "attributes": {
                "issue_type": {"value": issue_type, "data_type": "string"},
                "description": {"value": description, "data_type": "string"},
                "priority": {"value": priority, "data_type": "string"},
                "status": {"value": "open", "data_type": "string"},
            },
        }

        # Save to DynamoDB
        try:
            self.dynamo_adapter.put_item(ticket)
            # Refresh tickets list
            self._onload()
            # Return to tickets view
            asyncio.create_task(self.transition_view("view_all"))
        except Exception as e:
            print(f"Error creating ticket: {e}")
            # You might want to show an error message to the user here

    async def transition_view(self, new_view):
        """Handle view transitions with fade effects."""
        current_view = self.state.get("view")

        # Get current container
        current_container = (
            self.tickets_container
            if current_view == "view_all"
            else (
                self.create_ticket_container
                if current_view == "create_ticket"
                else None
            )
        )

        # Fade out current view
        if current_container:
            current_container.style(f"opacity: 0")
            await asyncio.sleep(self.fade_duration)

        # Update view state
        self.state.set("view", new_view)
        self.render_view.refresh()

        # Get new container
        new_container = (
            self.tickets_container
            if new_view == "view_all"
            else self.create_ticket_container if new_view == "create_ticket" else None
        )

        # Fade in new view
        if new_container:
            new_container.style(f"opacity: 0")
            await asyncio.sleep(0.1)  # Small delay to ensure DOM is updated
            new_container.style(f"opacity: 1")

    def on_click_create_ticket(self):
        """Handle create ticket button click with animation."""
        ui.run_javascript(
            """
            document.querySelectorAll('.transition-opacity').forEach(el => {
                el.style.transition = 'opacity 0.3s ease-in-out';
            });
        """
        )
        asyncio.create_task(self.transition_view("create_ticket"))

    @ui.refreshable
    def render_view(self):
        """Render the current view with fade effects."""
        view = self.state.get("view")

        if view == "view_all":
            self.render_tickets_table()
        elif view == "create_ticket":
            self.render_create_ticket()

    def content(self):
        with ui.column().classes("flex w-full h-[80vh]"):
            self.render_view()


def tickets_page(storage_manager):
    page = TicketsPage(storage_manager)
    page.render()
