from datetime import datetime
import pandas as pd
from nicegui import ui
from .BaseWGT import BaseWGT


class WGT_Operator_Performance_Analysis(BaseWGT):
    def __init__(
        self, dataframe_callback, widget_configuration=None, widget_instance_id=None
    ):
        self.get_dataframe = dataframe_callback
        super().__init__(widget_configuration, widget_instance_id)
        self.widget_id = "wgt_operator_performance_analysis"
        self.widget_name = "Collector Performance Analysis"
        self.widget_description = "Visualizes collector performance metrics including collections and contingency"
        self.widget_icon = "groups"

        self.transactions_df = None
        self.chart_data = None
        self._onload()

    def _onload(self):
        self._set_default_configuration()
        self._process_data()

    def _set_default_configuration(self):
        if not self.widget_configuration:
            self.widget_configuration = {
                "title": "Collector Performance Analysis",
                "chart_type": "column",
                "widget_width": 6,
                "show_contingency": True,
                "top_n_collectors": 10,
                "as_card": True,
            }

    def _process_data(self):
        # Load transactions data
        self.transactions_df = self.get_dataframe("datasets/primary/TR_Master.csv")

        # Group by operator and calculate metrics
        performance_metrics = (
            self.transactions_df.groupby("operator")
            .agg({"payment_amount": "sum", "contingency_amount": "sum"})
            .reset_index()
        )

        # Calculate total collections for percentage
        total_collections = performance_metrics["payment_amount"].sum()

        # Calculate percentage of total collections
        performance_metrics["percentage"] = (
            performance_metrics["payment_amount"] / total_collections * 100
        )

        # Sort by collections amount and get top N collectors
        top_n = int(self.widget_configuration.get("top_n_collectors", 10))
        performance_metrics = performance_metrics.nlargest(top_n, "payment_amount")

        # Prepare data for Highcharts
        self.chart_data = {
            "operators": performance_metrics["operator"].tolist(),
            "collections": performance_metrics["payment_amount"].tolist(),
            "contingency": performance_metrics["contingency_amount"].tolist(),
            "percentages": performance_metrics["percentage"].tolist(),
        }

    def widget_configuration_form(self):
        with ui.column().classes("w-full gap-4"):
            ui.input(
                label="Widget Title",
                value=self.widget_configuration.get(
                    "title", "Collector Performance Analysis"
                ),
                on_change=lambda e: self._update_configuration("title", e.value),
            ).classes("w-full")

            # Updated select element configuration
            ui.select(
                label="Chart Type",
                options={"column": "Column Chart", "bar": "Bar Chart"},
                value=self.widget_configuration.get("chart_type", "column"),
                on_change=lambda e: self._update_configuration("chart_type", e.value),
            ).classes("w-full")

            # Replace number input with slider
            ui.slider(
                min=3,
                max=10,
                step=1,
                value=self.widget_configuration.get("top_n_collectors", 5),
                on_change=lambda e: self._update_configuration(
                    "top_n_collectors", e.value
                ),
            ).classes("w-full").props("label label-always").bind_value_to(
                lambda: f"Top {self.widget_configuration.get('top_n_collectors', 5)} Collectors"
            )

            ui.switch(
                text="Show Contingency",
                value=self.widget_configuration.get("show_contingency", True),
                on_change=lambda e: self._update_configuration(
                    "show_contingency", e.value
                ),
            )
            ui.switch(
                text="As Card",
                value=self.widget_configuration.get("as_card", True),
                on_change=lambda e: self._update_configuration("as_card", e.value),
            )

    def _update_configuration(self, key, value):
        self.widget_configuration[key] = value
        if key == "top_n_collectors":
            self._process_data()
        self.create_widget()

    def widget_content(self):
        container_element = (
            ui.card().classes("w-full gap-4 rounded-lg")
            if self.widget_configuration.get("as_card", True)
            else ui.column().classes("w-full gap-4 p-[1rem]")
        )

        with container_element:
            ui.label(self.widget_configuration["title"]).classes("text-xl font-bold")

            # Prepare series for the chart
            series = [
                {
                    "name": "Collections",
                    "data": self.chart_data["collections"],
                    "tooltip": {"valuePrefix": "$", "valueDecimals": 2},
                }
            ]

            if self.widget_configuration.get("show_contingency", True):
                series.append(
                    {
                        "name": "Contingency",
                        "data": self.chart_data["contingency"],
                        "tooltip": {"valuePrefix": "$", "valueDecimals": 2},
                    }
                )

            # Add percentage as a line on secondary axis
            series.append(
                {
                    "name": "% of Total Collections",
                    "type": "spline",
                    "data": self.chart_data["percentages"],
                    "yAxis": 1,
                    "tooltip": {"valueSuffix": "%", "valueDecimals": 1},
                }
            )

            chart_options = {
                "chart": {
                    "type": self.widget_configuration.get("chart_type", "column"),
                    "height": "400px",
                },
                "title": {"text": None},
                "xAxis": {
                    "categories": self.chart_data["operators"],
                    "title": {"text": "Collectors"},
                },
                "yAxis": [
                    {
                        "title": {"text": "Amount ($)"},
                        "labels": {"format": "${value:,.0f}"},
                    },
                    {
                        "title": {"text": "% of Total Collections"},
                        "labels": {"format": "{value}%"},
                        "opposite": True,
                    },
                ],
                "plotOptions": {
                    "column": {"grouping": True, "shadow": False},
                    "spline": {"marker": {"enabled": True}},
                },
                "tooltip": {"shared": True},
                "legend": {
                    "align": "center",
                    "verticalAlign": "bottom",
                    "floating": False,
                },
                "series": series,
            }

            ui.highchart(chart_options).classes("w-full")

    def create_widget(self, widget_configuration=None):
        if widget_configuration:
            self.widget_configuration = widget_configuration
        elif not self.widget_configuration:
            self._set_default_configuration()

        if not self.widget_container:
            with ui.row().classes("w-full") as container:
                self.widget_container = container

        self.widget_container.clear()
        with self.widget_container:
            self.widget_content()
