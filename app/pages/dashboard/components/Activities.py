from nicegui import ui
from modules import StyleManager, ThemeManager
from components.widgets import *


class ActivitiesComponent:
    def __init__(self):
        self.theme_manager = ThemeManager()
        self.style_manager = StyleManager()
        self.force_refresh = False
        self._config()

    def _config(self):

        self.style_manager.set_styles(
            {
                "activities_component": {
                    "action_bar": """
                    display:flex;
                    justify-content:flex-end;
                    align-items:center;
                    padding:0.5rem;
                    width:100%;
                    height:2.5rem;
                    background-color:{self.theme_manager.get_color("base-color.white")};
                    border-radius:5px;
                    border:1px solid rgba(88,152,212,0.3);
                    box-shadow:0 0 0 1px rgba(88,152,212,0.2);
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

    def refresh_activities(self):
        self.force_refresh = True
        # Refresh the UI component
        self.render_activity_feed.refresh()

    @ui.refreshable
    def render_activity_feed(self):
        pass
        # collection_insights_widget = create_collection_insights_widget(
        #     force_refresh=self.force_refresh
        # )
        # collection_insights_widget.render()

        # portfolio_widget = create_portfolio_performance_widget(
        #     force_refresh=self.force_refresh
        # )
        # portfolio_widget.render()

        # effectiveness_widget = create_collection_effectiveness_widget(
        #     force_refresh=self.force_refresh
        # )
        # effectiveness_widget.render()

        # risk_scoring_widget = create_risk_scoring_widget(
        #     force_refresh=self.force_refresh
        # )
        # risk_scoring_widget.render()

        self.force_refresh = False

    def render(self):
        with ui.column().style(
            "width:100%;height:100%;padding-top:1rem;padding-bottom:1rem;padding-left:0.5rem;padding-right:0.5rem;"
        ):
            with ui.row().style(
                self.style_manager.get_style("activities_component.action_bar")
            ):
                ui.button(icon="refresh", on_click=self.refresh_activities).props(
                    "round size=sm"
                )
            with ui.column().style(
                self.style_manager.get_style("activities_component.activity_feed")
            ):
                with ui.scroll_area().style("width:100%;height:100%;"):
                    self.render_activity_feed()
