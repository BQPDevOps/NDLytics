from nicegui import ui
from core import StandardPage
from .components import *
from components import ActionBar
from .components.ListView import ListViewComponent
from .components.NewTicketForm import NewTicketFormComponent
from .components.KanbanView import KanbanViewComponent
from middleware.dynamo import DynamoMiddleware
from middleware.cognito import CognitoMiddleware
from config import config


class TicketsPage(StandardPage):
    def __init__(self, session_manager):
        super().__init__(
            session_manager,
            page_config={
                "page_title": "Tickets",
                "page_icon": "tickets",
                "page_route": "/tickets",
                "page_root_route": "/",
                "page_description": "Tickets",
                "nav_position": "top",
            },
        )
        self.dynamo_middleware = DynamoMiddleware(config.aws_tickets_table_name)
        self.cognito_middleware = CognitoMiddleware()
        self.state = {
            "active_view": "list",
            "selected_ticket": None,
            "tickets": self._get_tickets(),
        }
        self.new_ticket_form = NewTicketFormComponent(
            on_ticket_created=self.refresh_tickets
        )

    def _get_tickets(self):
        user_id = self.cognito_middleware.get_user_id()
        expression_values = {":uid": {"S": user_id}}

        response = self.dynamo_middleware.scan(
            filter_expression="contains(ticket_tags, :uid)",
            expression_attribute_values=expression_values,
        )
        return response

    def switch_view(self, view):
        self.state["active_view"] = view
        self.render_content.refresh()

    def on_select_ticket(self, ticket):
        self.state["selected_ticket"] = ticket
        self.render_content.refresh()

    def refresh_tickets(self):
        self.state["tickets"] = self._get_tickets()
        self.render_content.refresh()

    @ui.refreshable
    def render_content(self):
        with ui.element("transition").props(
            "appear enter-active-class='animated fadeIn' leave-active-class='animated fadeOut'"
        ).classes("w-full"):
            if self.state["active_view"] == "list":
                with ui.element("div").classes("list-container").style("width: 100%"):
                    ListViewComponent(self.state, self.on_select_ticket).render()

            elif self.state["active_view"] == "kanban":
                with ui.element("div").classes("kanban-container").style("width: 100%"):
                    KanbanViewComponent(
                        self.state, on_ticket_updated=self.refresh_tickets
                    ).render()

    def page_content(self):
        with ui.column().classes("w-full h-full p-4"):
            with ui.row().style("width:100%;"):
                ActionBar(
                    views=[
                        {"label": "List", "value": "list"},
                        {"label": "Kanban", "value": "kanban"},
                    ],
                    active_view=self.state["active_view"],
                    on_view_switch=self.switch_view,
                    actions=[
                        {
                            "icon": "add",
                            "label": "Add",
                            "on_click": lambda: self.new_ticket_form.open(),
                        }
                    ],
                ).render()
            self.render_content()


def tickets_page(session_manager):
    page = TicketsPage(session_manager)
    page.render()
