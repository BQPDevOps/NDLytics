from nicegui import ui
from core import StandardPage
from .components import *


class ReportsPage(StandardPage):
    def __init__(self, session_manager):
        super().__init__(
            session_manager,
            page_config={
                "page_title": "Reports",
                "page_icon": "reports",
                "page_route": "/reports",
                "page_root_route": "/",
                "page_description": "Reports",
                "nav_position": "top",
            },
        )
        self._on_page_load()

    def _on_page_load(self):
        self.container = ReportsContainer()

    def page_content(self):
        with ui.grid(columns=5).classes("w-full h-[89vh] gap-0"):
            with ui.column().classes("col-span-4 justify-center items-center"):
                self.container.render()


def reports_page(session_manager):
    page = ReportsPage(session_manager)
    page.render()
