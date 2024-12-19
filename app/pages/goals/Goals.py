from nicegui import ui
from core import StandardPage
from .components import *


class GoalsPage(StandardPage):
    def __init__(self, session_manager):
        super().__init__(
            session_manager,
            page_config={
                "page_title": "Goals",
                "page_icon": "flag",
                "page_route": "/goals",
                "page_root_route": "/",
                "page_description": "Goals",
                "nav_position": "top",
            },
        )
        self.state = {
            "selected_goal": None,
        }

    def on_click_select_goal(self, goal):
        self.state["selected_goal"] = goal
        self._render_goal_sidebar.refresh()
        self._render_goal_table.refresh()

    @ui.refreshable
    def _render_goal_sidebar(self):
        if self.state["selected_goal"]:
            goal_view_component = GoalViewComponent(
                self.session_manager, self.state, self.on_click_select_goal
            )
            goal_view_component.render()
        else:
            recent_activity_component = RecentActivityComponent(self.state)
            recent_activity_component.render()

    @ui.refreshable
    def _render_goal_table(self):
        goal_table_component = GoalTableComponent(
            self.session_manager, self.state, self.on_click_select_goal
        )
        goal_table_component.render()

    def page_content(self):
        with ui.grid(columns=4).style("width:100%;height:100%;gap:0"):
            with ui.column().classes("col-span-3 p-2").style(
                "border-right:1px solid rgba(192,192,192,0.3);box-shadow:0 0 0 1px rgba(192,192,192,0.3);"
            ):
                self._render_goal_table()
            with ui.column().classes("col-span-1 p-2").style(
                "border-right:1px solid rgba(192,192,192,0.3);box-shadow:0 0 0 1px rgba(192,192,192,0.3);"
            ):
                self._render_goal_sidebar()


def goals_page(session_manager):
    page = GoalsPage(session_manager)
    page.render()
