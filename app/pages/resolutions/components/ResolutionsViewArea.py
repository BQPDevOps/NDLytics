from nicegui import ui

from middleware.dynamo import DynamoMiddleware
from config import config


class ResolutionsViewArea:
    def __init__(self):
        self.dynamo = DynamoMiddleware(config.aws_requests_table_name)

    def render(self):
        with ui.column().classes("w-full h-full p-4"):
            with ui.card().classes("w-full h-full rounded-lg"):
                ui.label("View Area")
