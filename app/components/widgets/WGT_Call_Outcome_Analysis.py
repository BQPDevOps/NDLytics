from nicegui import ui
import pandas as pd
from decimal import Decimal


class WGT_Call_Outcome_Analysis:
    def __init__(
        self, dataframe_callback, widget_configuration=None, widget_instance_id=None
    ):
        self.get_dataframe = dataframe_callback
        self.widget_configuration = widget_configuration or {}
        self.widget_instance_id = widget_instance_id
        self.widget_id = "wgt_call_outcome_analysis"
        self.widget_name = "Call Outcome Analysis"
        self.widget_description = (
            "Analysis of call outcomes by result type and interaction"
        )
        self.widget_icon = "phone_callback"
        self.widget_width = self.widget_configuration.get("widget_width", 5)
        self.widget_container = None
        self.chart_data = []

        # Define result categories
        self.result_categories = {
            "Talked To Debtor": "Primary Contact",
            "Talked To Spouse": "Primary Contact",
            "Talked To Other": "Other Contact",
            "Talked to Co-Maker": "Other Contact",
            "Not In Service": "No Contact",
            "No Answer": "No Contact",
            "Answering Machine": "No Contact",
            "NONE": "No Contact",
        }

        self._set_default_configuration()
        self._process_data()

    def _set_default_configuration(self):
        if not self.widget_configuration:
            self.widget_configuration = {
                "title": "Call Outcomes by Interaction Type",
                "chart_type": "column",
                "as_card": True,
                "time_period": "all",
                "show_percentages": True,
            }

    def _process_data(self):
        # Get outbound calls data
        od_df = self.get_dataframe("datasets/primary/OD_Master.csv")

        # Filter by time period if needed
        if self.widget_configuration.get("time_period") != "all":
            od_df["Call_Date"] = pd.to_datetime(
                od_df["Call Completed Date"]
            ).dt.tz_localize(None)
            current_time = pd.Timestamp.now().tz_localize(None)

            if self.widget_configuration["time_period"] == "month":
                cutoff_date = current_time - pd.DateOffset(months=1)
                od_df = od_df[od_df["Call_Date"] >= cutoff_date]
            elif self.widget_configuration["time_period"] == "week":
                cutoff_date = current_time - pd.DateOffset(weeks=1)
                od_df = od_df[od_df["Call_Date"] >= cutoff_date]

        # Add category column
        od_df["Category"] = od_df["Interaction"].map(self.result_categories)

        # Group by category and result
        grouped_data = (
            od_df.groupby(["Category", "Result"]).size().unstack(fill_value=0)
        )

        # Calculate percentages if needed
        if self.widget_configuration.get("show_percentages", True):
            total_calls = grouped_data.sum().sum()
            grouped_data = (grouped_data / total_calls * 100).round(2)

        # Prepare series data
        self.chart_data = []
        for category in grouped_data.index:
            series_data = [
                {"name": result, "y": float(value)}
                for result, value in grouped_data.loc[category].items()
                if value > 0  # Only include non-zero values
            ]
            if series_data:  # Only add series if it has data
                self.chart_data.append({"name": category, "data": series_data})

    def widget_configuration_form(self):
        with ui.column().classes("w-full gap-4"):
            ui.input(
                label="Title",
                value=self.widget_configuration.get(
                    "title", "Call Outcomes by Interaction Type"
                ),
                on_change=lambda e: self._update_configuration("title", e.value),
            ).classes("w-full")

            ui.select(
                label="Chart Type",
                options={"column": "Column Chart", "bar": "Bar Chart"},
                value=self.widget_configuration.get("chart_type", "column"),
                on_change=lambda e: self._update_configuration("chart_type", e.value),
            ).classes("w-full")

            ui.select(
                label="Time Period",
                options={"all": "All Time", "month": "Last Month", "week": "Last Week"},
                value=self.widget_configuration.get("time_period", "all"),
                on_change=lambda e: self._update_configuration("time_period", e.value),
            ).classes("w-full")

            ui.switch(
                text="Show as Percentages",
                value=self.widget_configuration.get("show_percentages", True),
                on_change=lambda e: self._update_configuration(
                    "show_percentages", e.value
                ),
            )

            ui.switch(
                text="As Card",
                value=self.widget_configuration.get("as_card", True),
                on_change=lambda e: self._update_configuration("as_card", e.value),
            )

    def _update_configuration(self, key, value):
        self.widget_configuration[key] = value
        if key in ["chart_type", "time_period", "show_percentages"]:
            self._process_data()
        self.create_widget()

    def create_widget(self, widget_configuration=None):
        if widget_configuration:
            self.widget_configuration = widget_configuration
            self._process_data()

        if not self.widget_container:
            with (
                ui.card().classes("w-full gap-4 rounded-lg")
                if self.widget_configuration.get("as_card", True)
                else ui.column().classes("w-full gap-4 p-[1rem]")
            ) as container:
                self.widget_container = container

        self.widget_container.clear()

        with self.widget_container:
            ui.label(
                self.widget_configuration.get(
                    "title", "Call Outcomes by Interaction Type"
                )
            ).classes("text-xl font-bold mb-4")

            chart_type = self.widget_configuration.get("chart_type", "column")
            show_percentages = self.widget_configuration.get("show_percentages", True)

            chart_options = {
                "chart": {"type": chart_type},
                "title": {"text": ""},
                "xAxis": {"type": "category"},
                "yAxis": {
                    "title": {
                        "text": (
                            "Percentage of Calls"
                            if show_percentages
                            else "Number of Calls"
                        )
                    }
                },
                "plotOptions": {
                    "series": {
                        "stacking": "normal",
                        "dataLabels": {
                            "enabled": True,
                            "format": (
                                "{point.y:.1f}%"
                                if show_percentages
                                else "{point.y:,.0f}"
                            ),
                        },
                    }
                },
                "tooltip": {
                    "headerFormat": "<b>{series.name}</b><br/>",
                    "pointFormat": (
                        "{point.name}: <b>{point.y:.1f}%</b>"
                        if show_percentages
                        else "{point.name}: <b>{point.y:,.0f}</b>"
                    ),
                },
                "series": self.chart_data,
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
