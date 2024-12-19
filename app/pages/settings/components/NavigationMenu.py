from nicegui import ui


class NavigationMenu:
    def __init__(self, settings_state: dict, set_component: callable):
        self.menu_items = [
            {
                "name": "User Settings",
                "icon": "person",
                "component": "user_settings",
            },
            {
                "name": "Manage Users",
                "icon": "group",
                "component": "manage_users",
            },
            {
                "name": "Organization",
                "icon": "business",
                "component": "organization",
            },
        ]
        self.settings_state = settings_state
        self.set_component = set_component

    def _menu_item_on_click(self, item):
        self.set_component(item["component"])
        self._render_menu_items.refresh()

    @ui.refreshable
    def _render_menu_items(self):
        for item in self.menu_items:
            is_selected = self.settings_state["component"] == item["component"]
            background_color = (
                "rgb(230, 230, 230)" if is_selected else "rgb(250, 250, 250)"
            )
            with ui.item(on_click=lambda i=item: self._menu_item_on_click(i)).classes(
                "w-full hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer rounded-lg p-2 my-1 transition-all duration-300 ease-in-out transform"
                + (
                    " shadow-lg -translate-y-1"
                    if is_selected
                    else " border border-gray-200 translate-y-0"
                )
            ).style(f"background-color:{background_color}"):
                with ui.item_section().classes(
                    "text-gray-500 dark:text-gray-400"
                ).props("side"):
                    with ui.row().style(
                        "display:flex;justify-content:center;align-items:center;border-radius:50%;width:2.5rem;height:2.5rem;border:1px solid rgba(192,192,192,0.3);box-shadow:0 0 0 1px rgba(192,192,192,0.4);background-color:rgb(88 152 212)"
                    ):
                        ui.icon(item["icon"]).props("size=md color=white")
                with ui.item_section().classes(
                    "text-gray-700 dark:text-gray-200 w-full justify-center items-center"
                ):
                    ui.label(item["name"]).classes("text-lg")
                with ui.item_section().props("side").classes("text-gray-400"):
                    if is_selected:
                        ui.icon("chevron_right").props("size=lg color=teal")
                    else:
                        ui.icon("chevron_right").props("size=lg color=gray-400")

    def render(self):
        with ui.column().classes("w-full h-full py-1"):
            with ui.list().classes(
                "w-full h-full bg-white dark:bg-gray-800 rounded-lg shadow-md"
            ):
                self._render_menu_items()
