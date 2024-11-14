# shared/StaticPage.py

from nicegui import ui
from config import config
from components.common import DateTimeDisplay
from utils.helpers import cognito_adapter
from utils.lists import get_list
from theme import ThemeManager
from abc import ABC, abstractmethod


class StaticPage(ABC):
    def __init__(
        self,
        page_title,
        page_route,
        page_description,
        storage_manager,
        back_button_route=None,
        root_route=None,
    ):
        self.page_title = page_title
        self.page_route = page_route
        self.page_description = page_description
        self.storage_manager = storage_manager
        self.cognito_adapter = cognito_adapter()
        self.back_button_route = back_button_route
        self.theme_manager = ThemeManager()
        self.page_state = {}
        self.messages_count = 1
        self.root_route = root_route

        self.toolbar_items = {
            "menu": {
                "icon": "menu",
                "color": "blue",
                "direction": "left",
            },
            "submenu": [
                {
                    "icon": "o_logout",
                    "color": "blue-5",
                    "callback": lambda: self.cognito_adapter.signout(),
                }
            ],
        }
        self.navigation_items = get_list("page_routes")

    def page_state(self, method, key, value):
        if method == "set":
            self.page_state[key] = value
        elif method == "get":
            return self.page_state.get(key, None)
        elif method == "clear":
            self.page_state = {}

    def render_sidebar_navigation(self):
        # with ui.left_drawer(top_corner=True, bottom_corner=True).style(
        #     f"background-color: {self.theme_manager.colors['primary']['base']}; width: 240px !important;"
        # ):
        with ui.left_drawer(top_corner=True, bottom_corner=True).style(
            # f"background-color: {self.theme_manager.colors['primary']['base']}; width: 240px !important;"
            f"background: linear-gradient(22deg, rgba(0,68,102,1) 0%, rgba(0,68,102,1) 30%, rgba(0,131,196,1) 86%, rgba(0,90,135,1) 93%, rgba(0,82,124,1) 100%); width: 240px !important;"
        ):
            with ui.column().classes("flex h-screen w-full"):
                with ui.row().classes("flex justify-start items-center w-full"):
                    with ui.row().classes(
                        "w-full flex justify-center items-center"
                    ).style(f"overflow:hidden;background-color: transparent;"):
                        ui.image(
                            "static/images/branding/ndlytics_logo_dark.svg"
                        ).classes("w-2/3").style("height:40px;")
                    # with ui.row().classes("flex justify-center items-center w-full"):
                    #     DateTimeDisplay()
                    with ui.row().classes("flex justify-start items-center w-full"):
                        with ui.list().props("bordered separator").classes(
                            "w-full rounded-lg"
                        ):
                            for index, section in enumerate(self.navigation_items):
                                page_name = section["page_name"]
                                route = section["route"]
                                icon = section["icon"]
                                required_permissions = section.get(
                                    "required_permissions", []
                                )

                                # Check permissions for each item
                                if (
                                    not required_permissions
                                    or self.cognito_adapter.has_permission(
                                        required_permissions
                                    )
                                ):
                                    selected = (
                                        self.page_route == route
                                        or self.root_route == route
                                    )

                                    bg_color = (
                                        f"{self.theme_manager.colors['primary']['highlight']}"
                                        if selected
                                        else f"{self.theme_manager.colors['secondary']['base']}"
                                    )
                                    box_shadow = (
                                        "inset 0 0 10px rgba(255, 255, 255, 0.3)"
                                        if selected
                                        else ""
                                    )

                                    # Determine border radius based on visible items
                                    if index == 0:
                                        border_radius = "10px 10px 0 0"
                                    elif index == len(self.navigation_items) - 1:
                                        border_radius = "0 0 10px 10px"
                                    else:
                                        border_radius = "0"

                                    # Removed the is_root condition
                                    with ui.item(
                                        on_click=lambda p=route: ui.navigate.to(p)
                                    ).style(
                                        f"background-color: {bg_color}; color: white; box-shadow: {box_shadow}; border-radius: {border_radius};"
                                    ):
                                        with ui.item_section():
                                            ui.icon(icon).classes("text-xl").style(
                                                f"color: {self.theme_manager.get_color('basic', 'white')};"
                                            )
                                        with ui.item_section():
                                            ui.item_label(page_name)
                                else:
                                    # Debugging: Permission denied for this section
                                    print(f"Permission denied for section: {page_name}")

    def hex_to_rgba(self, hex_color: str, opacity_percentage: float) -> str:
        """
        Convert hex color to rgba format with specified opacity

        Args:
            hex_color (str): Hex color code (e.g. '#FF0000' or 'FF0000')
            opacity_percentage (float): Opacity value between 0 and 100

        Returns:
            str: rgba color string (e.g. 'rgba(255, 0, 0, 0.5)')
        """
        # Remove '#' if present
        hex_color = hex_color.lstrip("#")

        # Convert hex to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Convert opacity percentage to decimal (0-1)
        opacity = opacity_percentage / 100

        return f"rgba({r}, {g}, {b}, {opacity})"

    def render_toolbar(self):
        primary_menu = self.toolbar_items.get("menu")
        secondary_menu = self.toolbar_items.get("submenu")

        with ui.header().style(
            "background-color:#EEF4FA;display:flex;align-items:center;justify-content:center;height:8.5vh"
        ):
            with ui.row().classes("flex w-full").style("height:100%"):
                with ui.button(
                    on_click=lambda: ui.notify("Messages"),
                ).props("flat").style(
                    f"height:100%;border: 1px solid {self.hex_to_rgba(self.theme_manager.get_color('button-basic', 'base'), 30)};border-radius:2rem"
                ):
                    ui.icon("o_forum").classes("text-xl").style(
                        f"color: {self.theme_manager.get_color('button-basic')};"
                    )
                    if self.messages_count > 0:
                        ui.badge(self.messages_count, color="red").props("floating")
                ui.space()
                with ui.column().style(
                    "display:flex;justify-content:center;align-items:center;height:100%"
                ):
                    if self.back_button_route:
                        ui.button(
                            icon="arrow_back",
                            on_click=lambda: ui.navigate.to(self.back_button_route),
                        ).classes("bg-blue-5")
                ui.space()
                with ui.element("q-fab").props(
                    f"icon={primary_menu['icon']} color={primary_menu['color']} direction={primary_menu['direction']}"
                ):
                    for item in secondary_menu:
                        ui.element("q-fab-action").props(
                            f"icon={item['icon']} color={item['color']}"
                        ).on("click", item["callback"])
            ui.separator()

    @abstractmethod
    def content(self):
        pass

    def render(self):
        ui.add_head_html(
            """
            <style>
            header {
            left:240px !important;
            }
            aside {
                width: 240px !important;}
            .q-drawer--no-top-padding {
                width: 240px !important;
            }
            .q-page-container {
                padding-left: 240px !important;
            }
            main {
                background-color: #EEF4FA;
            }
            </style>
            """
        )

        if self.page_title:
            ui.page_title(self.page_title)
            self.render_toolbar()
            self.render_sidebar_navigation()
            self.content()
