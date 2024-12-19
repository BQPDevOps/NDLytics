from nicegui import ui
from abc import ABC, abstractmethod
from modules import StateManager, ListManager, StyleManager
from middleware.cognito.CognitoMiddleware import CognitoMiddleware

from pydantic import BaseModel
from typing import Optional, Callable


class MenuItemModel(BaseModel):
    icon: str
    title: str
    route: str
    callback: Optional[Callable] = None


class Menu:
    def __init__(self, current_route, menu_items):
        self.current_route = current_route
        self.menu_items = [MenuItemModel(**item) for item in menu_items]
        self.render()

    def render(self):
        with ui.row().style(
            "height:100%;display:flex;justify-content:flex-end;align-items:center;"
        ):
            for menu_item in self.menu_items:
                is_selected = self.current_route == menu_item.route

                def create_click_handler(menu_item):
                    return (
                        menu_item.callback
                        if menu_item.callback
                        else lambda: ui.navigate.to(menu_item.route)
                    )

                on_click_action = create_click_handler(menu_item)

                if is_selected:
                    ui.button(icon=menu_item.icon, on_click=on_click_action).props(
                        "round"
                    ).tooltip(menu_item.title)
                else:
                    ui.button(icon=menu_item.icon, on_click=on_click_action).props(
                        "round outline"
                    ).tooltip(menu_item.title)


class StandardPage(ABC):
    def __init__(self, session_manager, page_config):
        self.session_manager = session_manager
        self.list_manager = ListManager()
        self.cognito = CognitoMiddleware()
        self.style_manager = StyleManager()
        self.show_branding = True

        self.page_config = page_config
        self.page_title = page_config["page_title"]
        self.page_icon = page_config["page_icon"]
        self.page_description = page_config["page_description"]
        self.page_route = page_config["page_route"]
        self.page_root_route = page_config["page_root_route"]

        self.state = StateManager(f"{page_config['page_title']}_page_state")
        self.app_list = self.list_manager.get_list("app_list")

    def _build_page_navbar(self):
        with ui.card().tight().style(
            self.style_manager.get_style("standard_page.page_navbar")
        ):
            with ui.column().style(
                "width:10%;height:100%;display:flex;align-items:flex-start;justify-content:center;"
            ):
                ui.image("static/images/branding/ndlytics_logo_light.svg").style(
                    self.style_manager.get_style("standard_page.page_navbar_branding")
                )
            with ui.row().style(
                "gap:0.2rem !important;display:flex;flex:1;justify-content:flex-end;align-items:center;height:100%;"
            ):
                # for app in self.app_list:
                #     create_nav_button(app, self.page_route)
                Menu(self.page_route, self.app_list)

    def _build_page_content(self):
        self._build_page_navbar()
        self.page_content()

    def render(self):
        with ui.column().style(
            self.style_manager.get_style("standard_page.page_container")
        ):
            self._build_page_content()

    @abstractmethod
    def page_content(self):
        """Abstract method that must be implemented by child classes"""
        pass
