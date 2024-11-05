from nicegui import ui
from decimal import Decimal
import pandas as pd


class WGT_Call_Duration_Analysis:
    def __init__(
        self, dataframe_callback, widget_configuration=None, widget_instance_id=None
    ):
        self.get_dataframe = dataframe_callback
        self.widget_configuration = widget_configuration or {}
        self.widget_instance_id = widget_instance_id
        self.widget_id = "wgt_call_duration_analysis"
        self.widget_name = "Call Duration Analysis"
        self.widget_description = (
            "Analysis of average call durations by interaction type"
        )
        self.widget_icon = "phone_in_talk"
        self.widget_width = self.widget_configuration.get("widget_width", 6)
        self.widget_container = None
        self.chart_data = []

        self._set_default_configuration()
        self._process_data()

    def _set_default_configuration(self):
        if not self.widget_configuration:
            self.widget_configuration = {
                "title": "Average Call Duration by Interaction Type",
                "chart_type": "column",
                "as_card": True,
                "min_duration": 0,
                "show_all_interactions": True,
            }

    def _process_data(self):
        # Get the outbound calls data
        od_df = self.get_dataframe("datasets/primary/OD_Master.csv")

        # Calculate average duration for each interaction type
        avg_duration = (
            od_df.groupby("Interaction")["Delivery Length"]
            .mean()
            .round(2)
            .sort_values(ascending=False)
        )

        if not self.widget_configuration.get("show_all_interactions", True):
            # Filter out "NONE" and empty interactions if configured
            avg_duration = avg_duration[~avg_duration.index.isin(["NONE", ""])]

        # Filter by minimum duration if set
        min_duration = self.widget_configuration.get("min_duration", 0)
        avg_duration = avg_duration[avg_duration >= min_duration]

        # Convert seconds to minutes for better readability
        avg_duration = avg_duration / 60

        # Prepare data for Highcharts
        self.chart_data = [
            {"name": str(name), "y": float(duration)}
            for name, duration in avg_duration.items()
        ]

    def _update_configuration(self, key, value):
        self.widget_configuration[key] = value
        self._process_data()
        self.create_widget()

    def widget_configuration_form(self):
        with ui.column().classes("w-full gap-4"):
            ui.input(
                label="Chart Title",
                value=self.widget_configuration.get(
                    "title", "Average Call Duration by Interaction Type"
                ),
                on_change=lambda e: self._update_configuration("title", e.value),
            )
            ui.number(
                label="Minimum Duration (seconds)",
                value=self.widget_configuration.get("min_duration", 0),
                on_change=lambda e: self._update_configuration("min_duration", e.value),
            )
            ui.switch(
                text="Show All Interactions",
                value=self.widget_configuration.get("show_all_interactions", True),
                on_change=lambda e: self._update_configuration(
                    "show_all_interactions", e.value
                ),
            )
            ui.switch(
                text="As Card",
                value=self.widget_configuration.get("as_card", True),
                on_change=lambda e: self._update_configuration("as_card", e.value),
            )

    def create_widget(self, widget_configuration=None):
        if widget_configuration:
            self.widget_configuration = widget_configuration
            self._process_data()

        if not self.widget_container:
            with ui.column().classes("w-full") as container:
                self.widget_container = container

        self.widget_container.clear()

        with self.widget_container:
            # Transform data into separate series
            series_data = [
                {"name": item["name"], "data": [item["y"]], "type": "column"}
                for item in self.chart_data
            ]

            chart_options = {
                "chart": {"type": "column"},
                "title": {
                    "text": self.widget_configuration.get(
                        "title", "Average Call Duration by Interaction Type"
                    )
                },
                "xAxis": {
                    "type": "category",
                    "labels": {
                        "enabled": False  # Hide x-axis labels since we're using legend
                    },
                },
                "yAxis": {"title": {"text": "Average Duration (minutes)"}},
                "tooltip": {"pointFormat": "{series.name}: {point.y:.2f} minutes"},
                "legend": {
                    "layout": "horizontal",
                    "align": "center",
                    "verticalAlign": "bottom",
                    "enabled": True,
                },
                "plotOptions": {
                    "column": {
                        "dataLabels": {"enabled": True, "format": "{point.y:.1f}"},
                        "pointPadding": 0,
                        "groupPadding": 0,
                        "borderWidth": 0,
                    },
                    "series": {"showInLegend": True},
                },
                "series": series_data,
            }

            ui.highchart(chart_options).classes("w-full h-96")

    def get_widget_details(self):
        return {
            "widget_id": self.widget_id,
            "widget_instance_id": self.widget_instance_id,
            "widget_name": self.widget_name,
            "widget_description": self.widget_description,
            "widget_configuration": self.widget_configuration,
        }
