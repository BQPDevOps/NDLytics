from nicegui import ui
from modules import StyleManager, ThemeManager
from components.widgets import *


class ActivitiesComponent:
    def __init__(self):
        self.theme_manager = ThemeManager()
        self.style_manager = StyleManager()
        self.force_refresh = False
        self.active_view = "strategy"
        self.widgets = {}  # Store widget instances
        self._config()
        self._init_widgets()

    def _config(self):

        self.style_manager.set_styles(
            {
                "activities_component": {
                    "action_bar": """
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0 0.5rem;
                    width: 100%;
                    height: 2.5rem;
                    background-color:{self.theme_manager.get_color("base-color.white")};
                    border-radius: 5px;
                    border: 1px solid rgba(88,152,212,0.3);
                    box-shadow: 0 0 0 1px rgba(88,152,212,0.2);
                    """,
                    "activity_feed": """
                    width:100%;
                    height:100%;
                    background-color:#FFFFFF;
                    border:1px solid rgba(88,152,212,0.15);
                    border-radius:5px;
                    """,
                }
            }
        )

    def _init_widgets(self):
        # Initialize all widgets
        self.widgets["collection_insights"] = create_collection_insights_widget(
            force_refresh=self.force_refresh
        )
        self.widgets["collection_effectiveness"] = (
            create_collection_effectiveness_widget(force_refresh=self.force_refresh)
        )
        self.widgets["client_metrics"] = create_client_metrics_widget(
            force_refresh=self.force_refresh
        )
        self.widgets["placement_metrics"] = create_placement_metrics_widget(
            force_refresh=self.force_refresh
        )

    def refresh_activities(self):
        self.force_refresh = True
        # Refresh the UI component
        self.render_activity_feed.refresh()

    def switch_view(self, view):
        self.active_view = view
        self.render_action_bar.refresh()
        self.render_activity_feed.refresh()

    @ui.refreshable
    def render_action_bar(self):
        with ui.row():
            for view, label in [
                ("strategy", "Strategy"),
                ("performance", "Performance"),
                ("insights", "Insights"),
            ]:
                is_active = self.active_view == view
                ui.button(label, on_click=lambda v=view: self.switch_view(v)).props(
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
        # ui.button(icon="refresh", on_click=self.refresh_activities).props(
        #     "round size=sm"
        # )

    @ui.refreshable
    def render_activity_feed(self):
        with ui.element("transition").props(
            "appear enter-active-class='animated fadeIn' leave-active-class='animated fadeOut'"
        ).classes("w-full"):
            if self.active_view == "strategy":
                with ui.element("div").classes("strategy-container").style(
                    "width: 100%"
                ):
                    self.widgets["collection_effectiveness"].render()

            elif self.active_view == "performance":
                with ui.element("div").classes("performance-container").style(
                    "width: 100%"
                ):
                    self.widgets["placement_metrics"].render()
                    self.widgets["client_metrics"].render()

            elif self.active_view == "insights":
                with ui.element("div").classes("insights-container").style(
                    "width: 100%"
                ):
                    self.widgets["collection_insights"].render()

    def render(self):
        with ui.column().style(
            "width:100%;height:100%;padding-top:1rem;padding-bottom:1rem;padding-left:0.5rem;padding-right:0.5rem;"
        ):
            with ui.row().style(
                self.style_manager.get_style("activities_component.action_bar")
            ):
                self.render_action_bar()
            with ui.column().style(
                self.style_manager.get_style("activities_component.activity_feed")
            ):
                with ui.scroll_area().style("width:100%;height:100%;"):
                    self.render_activity_feed()
