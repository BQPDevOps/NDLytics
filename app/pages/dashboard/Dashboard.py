from nicegui import ui
from modules import DataProcessingManager
from core import StandardPage

from components.widgets import *
from .components import *


class DashboardPage(StandardPage):
    def __init__(self, session_manager):
        super().__init__(
            session_manager,
            page_config={
                "page_title": "Dashboard",
                "page_icon": "dashboard",
                "page_route": "/dashboard",
                "page_root_route": "/",
                "page_description": "Dashboard",
                "nav_position": "top",
            },
        )
        self.data_processor = DataProcessingManager()
        self.goals_component = GoalsComponent(session_manager)
        self.tasks_component = TasksComponent(session_manager)
        self.tickets_component = TicketsComponent()
        self.activities_component = ActivitiesComponent()

    def page_content(self):
        with ui.grid(columns=4).style("width:100%;height:89vh;gap:0"):
            with ui.column().classes("col-span-1 p-2 max-h-[89vh]").style(
                "border-right:1px solid rgba(192,192,192,0.3);box-shadow:0 0 0 1px rgba(192,192,192,0.3);"
            ):
                with ui.grid(rows=2).classes("w-full flex-grow"):
                    self.goals_component.render()
                    self.tickets_component.render()
            with ui.column().classes("col-span-2 p-2 max-h-[89vh]").style(
                "border-right:1px solid rgba(192,192,192,0.3);box-shadow:0 0 0 1px rgba(192,192,192,0.3);"
            ):
                self.activities_component.render()
            with ui.column().classes("col-span-1 p-2 max-h-[89vh]").style(
                "border-left:1px solid rgba(192,192,192,0.3);box-shadow:0 0 0 1px rgba(192,192,192,0.3);"
            ):
                with ui.grid(rows=2).classes("w-full flex-grow"):
                    self.tasks_component.render()


def dashboard_page(session_manager):
    page = DashboardPage(session_manager)
    page.render()
