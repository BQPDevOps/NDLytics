from nicegui import ui
from core import StandardPage
from .components import *


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
        self.state = {
            "selected_ticket": None,
        }

    def on_click_select_ticket(self, ticket):
        self.state["selected_ticket"] = ticket
        self._render_ticket_sidebar.refresh()

    @ui.refreshable
    def _render_ticket_sidebar(self):
        if self.state["selected_ticket"]:
            ticket_view_component = TicketViewComponent(self.state)
            ticket_view_component.render()
        else:
            recent_activity_component = RecentActivityComponent(self.state)
            recent_activity_component.render()

    def page_content(self):
        ticket_table_component = TicketTableComponent(
            self.state, self.on_click_select_ticket
        )

        with ui.grid(columns=4).style("width:100%;height:100%;gap:0"):
            with ui.column().classes("col-span-3 p-2").style(
                "border-right:1px solid rgba(192,192,192,0.3);box-shadow:0 0 0 1px rgba(192,192,192,0.3);"
            ):
                ticket_table_component.render()
            with ui.column().classes("col-span-1 p-2").style(
                "border-right:1px solid rgba(192,192,192,0.3);box-shadow:0 0 0 1px rgba(192,192,192,0.3);"
            ):
                self._render_ticket_sidebar()


def tickets_page(session_manager):
    page = TicketsPage(session_manager)
    page.render()
