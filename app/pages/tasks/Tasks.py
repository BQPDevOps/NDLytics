from nicegui import ui
from core import StandardPage
from .components import *


class TasksPage(StandardPage):
    def __init__(self, session_manager):
        super().__init__(
            session_manager,
            page_config={
                "page_title": "Tasks",
                "page_icon": "tasks",
                "page_route": "/tasks",
                "page_root_route": "/",
                "page_description": "Tasks",
                "nav_position": "top",
            },
        )
        self.state = {
            "selected_task": None,
        }

    def on_click_select_task(self, task):
        self.state["selected_task"] = task
        self._render_task_sidebar.refresh()

    @ui.refreshable
    def _render_task_sidebar(self):
        if self.state["selected_task"]:
            task_view_component = TaskViewComponent(self.state)
            task_view_component.render()
        else:
            recent_activity_component = RecentActivityComponent(self.state)
            recent_activity_component.render()

    def page_content(self):
        task_table_component = TaskTableComponent(self.state, self.on_click_select_task)

        with ui.grid(columns=4).style("width:100%;height:100%;gap:0"):
            with ui.column().classes("col-span-3 p-2").style(
                "border-right:1px solid rgba(192,192,192,0.3);box-shadow:0 0 0 1px rgba(192,192,192,0.3);"
            ):
                task_table_component.render()
            with ui.column().classes("col-span-1 p-2").style(
                "border-right:1px solid rgba(192,192,192,0.3);box-shadow:0 0 0 1px rgba(192,192,192,0.3);"
            ):
                self._render_task_sidebar()


def tasks_page(session_manager):
    page = TasksPage(session_manager)
    page.render()
