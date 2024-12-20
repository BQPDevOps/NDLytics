from nicegui import ui
from core import StandardPage
from .components import *


class InteliDocPage(StandardPage):
    def __init__(self, session_manager):
        super().__init__(
            session_manager,
            page_config={
                "page_title": "InteliDoc",
                "page_icon": "intelidoc",
                "page_route": "/intelidoc",
                "page_root_route": "/",
                "page_description": "InteliDoc",
                "nav_position": "top",
            },
        )
        self._on_page_load()

    def _on_page_load(self):
        self.chat_viewer = ChatViewer()
        self.doc_viewer = DocViewer()

    def page_content(self):
        with ui.grid(columns=5).classes("w-full h-[89vh] gap-0"):
            with ui.column().classes("col-span-2 justify-center items-center"):
                self.chat_viewer.render()
            with ui.column().classes("col-span-3 justify-center items-center"):
                self.doc_viewer.render()


def intelidoc_page(session_manager):
    page = InteliDocPage(session_manager)
    page.render()
