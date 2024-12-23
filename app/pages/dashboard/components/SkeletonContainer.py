from nicegui import ui, run
from typing import Any
import asyncio
import time


class SkeletonContainer:
    def __init__(self, widget_name: str, widget: Any):
        self.widget_name = widget_name
        self.widget = widget
        self.is_loading = True

    @ui.refreshable
    def render_content(self):
        with ui.card().tight().classes("w-full"):
            if self.is_loading:
                ui.skeleton(square=True, animation="wave", height="150px", width="100%")
                with ui.card_section().classes("w-full"):
                    ui.skeleton("text").classes("text-subtitle1")
                    ui.skeleton("text").classes("text-subtitle1 w-1/2")
            else:
                self.widget.render()

    async def load(self):
        self.is_loading = True
        self.render_content.refresh()

        def delay_operation():
            time.sleep(0.1)
            return True

        await run.io_bound(delay_operation)
        self.is_loading = False
        self.render_content.refresh()

    def render(self):
        self.render_content()
        asyncio.create_task(self.load())
