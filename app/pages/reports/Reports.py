from nicegui import ui
from core import StandardPage


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

    def page_content(self):
        pass


def reports_page(session_manager):
    page = ReportsPage(session_manager)
    page.render()
