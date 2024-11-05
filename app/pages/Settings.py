from nicegui import ui

from components.shared import StaticPage
from models import ManagedState
from utils.lists import get_list
from components.common import GridCard
from static.css import grid_card_animation


class SettingsPage(StaticPage):
    def __init__(self, storage_manager):
        super().__init__(
            page_title="Settings",
            page_route="/settings",
            page_description="Settings",
            storage_manager=storage_manager,
        )
        self.state = ManagedState("settings")
        self.state.set("view_list", get_list("user_settings_routes"))
        self.state.set("active_view", "default_view")

    def transition_content_view(self):
        render_view = self.state.get("active_view")
        view_map = {
            "default_view": self._default_view,
            "user_settings": self._user_settings,
            "ticket_system_settings": self._ticket_system_settings,
        }

        # Get the corresponding render function or use a default
        render_function = view_map.get(render_view, "default_view")
        render_function()

    def _default_view(self):
        with ui.grid(columns=4).style("width:100%;height:100%;"):
            for index, grid_item in enumerate(self.state.get("view_list")):
                GridCard(**grid_item, index=index).render()

    def _user_settings(self):
        pass

    def _ticket_system_settings(self):
        pass

    def content(self):
        ui.add_head_html(grid_card_animation)
        self.transition_content_view()


def settings_page(storage_manager):
    page = SettingsPage(storage_manager)
    page.render()
