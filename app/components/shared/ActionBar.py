from nicegui import ui
from modules import StyleManager, ThemeManager


class ActionBar:
    """
    Represents an action bar component for the application.
    It manages the display of actions and views within the application.
    """

    def __init__(
        self,
        title: str = "",
        actions: list = None,
        views: list = None,
        active_view: str = None,
        on_view_switch=None,
    ):
        """
        Initializes the ActionBar component.

        :param title: The title of the action bar.
        :param actions: A list of actions to be displayed in the action bar.
        :param views: A list of views to be displayed in the action bar.
        :param active_view: The currently active view.
        :param on_view_switch: A callback function to be called when the view is switched.
        """
        self.title = title
        self.actions = actions or []
        self.views = self._format_views(views or [])
        self.active_view = active_view
        self.on_view_switch = on_view_switch
        self.style_manager = StyleManager()
        self.theme_manager = ThemeManager()
        self._config()

    def _format_views(self, views: list) -> list:
        """
        Formats views to ensure they are in the correct dictionary format.
        If a string is provided, converts it to the dictionary format.
        """
        formatted_views = []
        for view in views:
            if isinstance(view, str):
                formatted_views.append({"label": view.capitalize(), "value": view})
            elif isinstance(view, dict) and "value" in view:
                if "label" not in view:
                    view["label"] = view["value"].capitalize()
                formatted_views.append(view)
        return formatted_views

    def _config(self):
        self.style_manager.set_styles(
            {
                "action_bar": {
                    "container": """
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0 0.5rem;
                width: 100%;
                height: 2.5rem;
                background-color:#FFFFFF;
                border-radius: 5px;
                border: 1px solid rgba(88,152,212,0.3);
                box-shadow: 0 0 0 1px rgba(88,152,212,0.2);
                """
                }
            }
        )

    def switch_view(self, view):
        """
        Switches the active view to the specified view.

        :param view: The view to switch to.
        """
        self.active_view = view
        if self.on_view_switch:
            self.on_view_switch(view)
        self.render_views.refresh()

    @ui.refreshable
    def render_views(self):
        """
        Renders the views in the action bar.
        """
        if self.views:
            with ui.row():
                for view in self.views:
                    is_active = self.active_view == view["value"]
                    ui.button(
                        view["label"],
                        on_click=lambda v=view["value"]: self.switch_view(v),
                    ).props(
                        f"flat size=sm {'text-primary' if is_active else ''}"
                    ).style(
                        f"""
                        font-size: 0.9rem;
                        color: {'#1976D2' if is_active else '#666'};
                        font-weight: {'500' if is_active else '400'};
                        border-bottom: {'2px solid #1976D2' if is_active else 'none'};
                        border-radius: 0;
                    """
                    )

    def render(self):
        """
        Renders the action bar component.
        """
        with ui.row().style(self.style_manager.get_style("action_bar.container")):
            if self.views:
                self.render_views()
            else:
                with ui.row():
                    ui.label(self.title).style(
                        "font-size: 0.9rem; color: #666; font-weight: 400;"
                    )
            with ui.row().classes("gap-2"):
                for action in self.actions:
                    if "icon" in action:
                        ui.button(
                            icon=action["icon"], on_click=action["on_click"]
                        ).props("round size=sm")
                    else:
                        ui.button(action["label"], on_click=action["on_click"]).props(
                            "flat size=sm"
                        )
