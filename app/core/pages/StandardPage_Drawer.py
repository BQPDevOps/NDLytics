from nicegui import ui
from abc import ABC, abstractmethod
from modules import StateManager, ListManager, StyleManager
from middleware.cognito.CognitoMiddleware import CognitoMiddleware
from components import create_nav_button


class StandardPage(ABC):
    def __init__(self, session_manager, page_config):
        self.session_manager = session_manager
        self.list_manager = ListManager()
        self.cognito = CognitoMiddleware()
        self.style_manager = StyleManager()
        self.header_content = None
        self.show_drawer_nav = True
        self.drawer_content = None
        self.show_branding = True

        self.page_config = page_config
        self.page_title = page_config["page_title"]
        self.page_icon = page_config["page_icon"]
        self.page_description = page_config["page_description"]
        self.page_route = page_config["page_route"]
        self.page_root_route = page_config["page_root_route"]
        self.nav_position = page_config["nav_position"]

        self.state = StateManager(f"{page_config['page_title']}_page_state")
        self.app_list = self.list_manager.get_list("app_list")
        self.right_drawer = None
        self.drawer_is_open = False

        self.app_list = self.list_manager.get_list("app_list")

        with ui.right_drawer(fixed=False).style(
            "background-color: transparent"
        ) as right_drawer:
            self._build_right_drawer()
            self.right_drawer = right_drawer

        # Override placeholders
        self.override_drawer_content = None
        self.override_header_content = None

    def set_drawer_visibility(self, show: bool):
        self.show_drawer_nav = show

    def set_drawer_content(self, content_function, branding=True):
        self.drawer_content = content_function
        self.show_branding = branding
        self.show_drawer_nav = False
        if self.right_drawer:
            with self.right_drawer:
                self._build_right_drawer.refresh()

    def set_header(self, content_function):
        """Set custom header content"""
        self.header_content = content_function
        self._build_page_header.refresh()

    def set_drawer(self, content_function):
        """Set custom drawer content"""
        self.drawer_content = content_function
        self.show_drawer_nav = False
        self._build_right_drawer.refresh()

    def toggle_drawer(self):
        """Toggle drawer open/closed"""
        self.drawer_is_open = not self.drawer_is_open
        self.right_drawer.toggle()

    def open_drawer(self):
        """Open drawer"""
        if not self.drawer_is_open:
            self.toggle_drawer()

    def close_drawer(self):
        """Close drawer"""
        if self.drawer_is_open:
            self.toggle_drawer()

    def show_drawer_branding(self, show: bool):
        """Toggle drawer branding visibility"""
        self.show_branding = show
        self._build_right_drawer.refresh()

    def set_drawer_override(self, branding=True):
        """Override method to be implemented by child class to set drawer content"""
        pass

    def set_header_override(self):
        """Override method to be implemented by child class to set header content"""
        pass

    def set_drawer_apps(self, apps_list: list = None):
        """Override the apps shown in drawer navigation
        Args:
            apps_list (list): List of dicts with keys: icon, title, color, route
                            If None, restores default apps list
        """
        if apps_list:
            self.apps = apps_list
        else:
            self.apps = self._default_apps.copy()

        # Ensure drawer nav is shown when setting apps
        self.show_drawer_nav = True
        self.drawer_content = None  # Clear any custom drawer content
        self._build_right_drawer.refresh()

    @ui.refreshable
    def _build_right_drawer(self):
        with ui.column().style(
            self.style_manager.get_style("standard_page.drawer_container")
        ):
            if self.show_branding:
                with ui.column().style(
                    "width:100%;display:flex;flex-direction:column;align-items:center;gap:0;"
                ):
                    with ui.row().style(
                        "width:100%;display:flex;justify-content:center;align-items:center;"
                    ):
                        with ui.column().style(
                            """
                                border-radius:0 0 10px 10px;
                                width:80%;
                                display:flex;background-color:#ffffff;
                                padding:0.5rem;
                                justify-content:center;
                                align-items:center;
                            """
                        ):
                            ##TODO: Branding should be dynamic setup in settings or company table
                            ui.image(
                                "static/images/branding/ndlytics_logo_light.svg"
                            ).style("width:80%;height:4rem;")
                ui.separator().classes("my-4")

            if self.drawer_content:
                self.drawer_content()
            elif self.show_drawer_nav:
                with ui.column().classes("w-full justify-start items-center px-4"):
                    ui.label("Applications").style(
                        "font-size:1.2rem;font-weight:bold;color:rgb(120,120,120);"
                    )
                    with ui.column().style(
                        "width:100%;height:100%;border:1px solid rgba(192,192,192,0.3);border-radius:10px;padding:0;"
                    ):
                        with ui.row().style(
                            "width:100%;display:flex;flex-wrap:wrap;gap:0.5rem;margin:0;padding:0;justify-content:center;padding-top:1rem;padding-bottom:1rem;"
                        ):

                            for app in self.app_list:
                                with ui.column().style(
                                    "width:40%;max-width:40%;padding:0;margin:0;"
                                ):
                                    create_nav_button(app, self.page_route)
                ui.space()
                with ui.row().classes(
                    "w-full flex justify-center items-center p-2 gap-2"
                ):
                    ui.button("LOGOUT", on_click=lambda: self.cognito.signout()).props(
                        "flat"
                    ).style("border:1px solid rgba(192,192,192,0.3);width:100%;")
            elif hasattr(self, "set_drawer_override"):
                self.set_drawer_override()

    @ui.refreshable
    def _build_page_header(self):
        with ui.row().style(
            "width:100%;background-color:rgba(255,255,255,0.8);border:1px solid rgba(192,192,192,0.3);border-radius:10px 10px 0 0;display:flex;align-items:center;justify-content:flex-end"
        ):
            if hasattr(self, "set_header_override"):
                self.set_header_override()
            else:
                ui.space()
                ui.button(icon="apps", on_click=self.toggle_drawer).props(
                    "flat size=xl"
                )

    def _build_page_content(self):
        self._build_page_header()
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
