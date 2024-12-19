from nicegui import ui
from core import StandardPage
from .components import *


class SettingsPage(StandardPage):
    def __init__(self, session_manager):
        super().__init__(
            session_manager,
            page_config={
                "page_title": "Settings",
                "page_icon": "settings",
                "page_route": "/settings",
                "page_root_route": "/",
                "page_description": "Settings",
                "nav_position": "top",
            },
        )
        self.settings_state = {
            "component": "user_settings",
        }
        self.navigation_menu = NavigationMenu(self.settings_state, self._set_component)
        self.user_settings_component = UserSettingsComponent(session_manager)
        self.manage_users_component = ManageUsersComponent(session_manager)
        self.organization_component = OrganizationComponent(session_manager)

    def _set_component(self, component: str):
        self.settings_state["component"] = component
        self._render_component.refresh()

    @ui.refreshable
    def _render_component(self):
        if self.settings_state["component"] == "user_settings":
            self.user_settings_component.render()
        elif self.settings_state["component"] == "manage_users":
            self.manage_users_component.render()
        elif self.settings_state["component"] == "organization":
            self.organization_component.render()

    def page_content(self):
        with ui.grid(columns=6).style("width:100%;height:89vh;gap:0"):
            with ui.column().classes("col-span-1 p-2 max-h-[89vh]").style(
                "border-right:1px solid rgba(192,192,192,0.3);box-shadow:0 0 0 1px rgba(192,192,192,0.3);"
            ):
                self.navigation_menu.render()
            with ui.column().classes("col-span-5 p-2 max-h-[89vh]").style(
                "border-left:1px solid rgba(192,192,192,0.3);box-shadow:0 0 0 1px rgba(192,192,192,0.3);"
            ):
                self._render_component()


def settings_page(session_manager):
    page = SettingsPage(session_manager)
    page.render()
