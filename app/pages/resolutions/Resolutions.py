from nicegui import ui
from core import StandardPage
from .components import *


class ResolutionsPage(StandardPage):
    def __init__(self, session_manager):
        super().__init__(
            session_manager,
            page_config={
                "page_title": "Resolutions",
                "page_icon": "handshake",
                "page_route": "/resolutions",
                "page_root_route": "/",
                "page_description": "Resolutions",
                "nav_position": "top",
            },
        )
        self._on_page_load()

    def _on_page_load(self):
        self.navbar = ResolutionsNavbar()
        self.view_area = ResolutionsViewArea()

    def page_content(self):
        with ui.grid(columns=5).classes("w-full h-[89vh] gap-0"):
            with ui.column().classes("col-span-1 justify-center items-center"):
                self.view_area.render()
            with ui.column().classes("col-span-4 justify-center items-center"):
                self.navbar.render()


def resolutions_page(session_manager):
    page = ResolutionsPage(session_manager)
    page.render()
