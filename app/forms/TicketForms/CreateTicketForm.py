from nicegui import ui
from models import ManagedState


class NewTicket:
    def __init__(
        self,
        uuid,
        status,
        priority,
        assigned_to,
        category,
        subcategory,
        description,
        created_at,
        created_by,
        updated_at,
        updated_by,
        history,
    ):
        self.uuid = uuid
        self.status = status
        self.priority = priority
        self.assigned_to = assigned_to
        self.category = category
        self.subcategory = subcategory
        self.description = description
        self.created_at = created_at
        self.created_by = created_by
        self.updated_at = updated_at
        self.updated_by = updated_by
        self.history = history


class CreateTicketForm:
    def __init__(self):
        self.state = ManagedState("create_ticket_form")

    def content(self):
        with ui.column().classes("w-full h-full"):
            ui.label("Create Ticket").classes("text-h6 q-mb-md")
            ui.input(label="Description").classes("w-full")

    def render(self):
        self.content()
