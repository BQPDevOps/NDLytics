from nicegui import ui
from core import StandardPage
from datetime import datetime
import json
from enum import Enum
import boto3

from middleware.cognito import create_cognito_middleware
from middleware.dynamo import create_dynamo_middleware


class DashboardView:
    def __init__(self):
        pass

    def render(self):
        with ui.grid(columns=4).classes("w-full h-[100%]"):
            with ui.column():
                ui.label("Column 1")
            with ui.column():
                ui.label("Column 2")
            with ui.column():
                ui.label("Column 3")
            with ui.column():
                ui.label("Column 4")


class ViewManager:
    def __init__(self):
        self.view_states = {
            "dashboard": DashboardView(),
        }
        self.view_state = "dashboard"

    def get_view(self, view_name):
        return self.view_states.get(view_name, None)

    def set_view(self, view_name):
        self.view_state = view_name

    @ui.refreshable
    def render_view(self):
        self.get_view(self.view_state).render()


class RequestsPage(StandardPage):
    def __init__(self, session_manager):
        super().__init__(
            session_manager,
            page_config={
                "page_title": "Requests",
                "page_icon": "requests",
                "page_route": "/requests",
                "page_root_route": "/",
                "page_description": "Requests",
            },
        )

        self.cognito_middleware = create_cognito_middleware()
        self.dynamo_middleware_requests = create_dynamo_middleware(
            "ResolutionRecord-nuvscsu2mzh4thewf2tsj7evu4-dev"
        )
        self.dynamo_middleware_loans = create_dynamo_middleware(
            "LoanRecord-nuvscsu2mzh4thewf2tsj7evu4-dev"
        )

    def page_content(self):
        pass


def requests_page(session_manager):
    page = RequestsPage(session_manager)
    page.render()
