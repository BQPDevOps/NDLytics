from nicegui import ui
import pandas as pd


class BaseWGT:  # Name of the widget
    def __init__(self, widget_configuration=None, widget_instance_id=None):  # REQUIRED
        self.widget_configuration = widget_configuration or {}  # REQUIRED
        self.widget_instance_id = widget_instance_id  # REQUIRED
        self.widget_width = self.widget_configuration.get(
            "widget_width", 10
        )  # REQUIRED
        self.widget_id = "base_wgt"  # REQUIRED
        self.widget_name = "Base Widget"  # REQUIRED
        self.widget_description = "Base Widget Description"  # REQUIRED
        self.widget_icon = "widgets"  # REQUIRED
        self.widget_container = None  # REQUIRED

        self._set_default_configuration()  # REQUIRED

    def _set_default_configuration(self):  # REQUIRED
        """Set the default configuration for the widget"""
        pass

    def _process_data(self):  # REQUIRED
        """Retrieve and process the data for the widget"""
        pass

    def widget_configuration_form(self):  # REQUIRED
        """Create the configuration form for the widget - UI elements - Handles providing UI user can use to customize different aspects of the widget"""
        pass

    def widget_content(self):  # REQUIRED
        """Create the content of the widget - UI elements"""
        pass

    def get_widget_details(self):  # REQUIRED
        """Get the details of the widget - BASE EXAMPLE"""
        return {
            "widget_id": self.widget_id,
            "widget_instance_id": self.widget_instance_id,
            "widget_name": self.widget_name,
            "widget_description": self.widget_description,
            "widget_configuration": self.widget_configuration,
        }

    def create_widget(self, widget_configuration=None):  # REQUIRED
        """Handle the creation of the widget and orchestration of UI elements if not done in the widget_content"""
        pass


class EXAMPLE_WGT:
    def __init__(
        self, dataframe_callback, widget_configuration=None, widget_instance_id=None
    ):
        self.get_dataframe = dataframe_callback
        self.widget_id = "wgt_creditor_balance_chart"
        self.widget_name = "Creditor Balance Distribution Chart"
        self.widget_description = (
            "Highcharts visualization of account balances by creditor"
        )
        self.widget_icon = "pie_chart"
        self.widget_width = 6

        self.widget_configuration = widget_configuration or {}
        self.widget_instance_id = widget_instance_id
        self.widget_container = None

        self.accounts_df = None
        self.chart_data = []

        self._onload()

    def _onload(self):
        self._process_data()

    def _process_data(self):
        self.accounts_df = self.get_dataframe("datasets/primary/AC_Master.csv")
        # Group by creditor and sum the balances
        creditor_balances = (
            self.accounts_df.groupby("creditor")["balance"]
            .sum()
            .sort_values(ascending=False)
        )

        # Take top 10 creditors and group the rest as "Others"
        top_creditors = creditor_balances.head(10)
        others = pd.Series({"Others": creditor_balances.iloc[10:].sum()})
        final_data = pd.concat([top_creditors, others])

        # Prepare data for Highcharts
        self.chart_data = [
            {"name": name, "y": float(value)} for name, value in final_data.items()
        ]

    def _set_default_configuration(self):
        if not self.widget_configuration:
            self.widget_configuration = {
                "title": "Account Balance Distribution by Creditor",
                "chart_type": "pie",
                "widget_width": 6,
            }

    def widget_configuration_form(self):
        with ui.column().style("display:flex;width:100%;height:100%"):
            ui.input(
                label="Title",
                value=self.widget_configuration.get(
                    "title", "Account Balance Distribution by Creditor"
                ),
                on_change=lambda e: self._update_configuration("title", e.value),
            ).style("width:100%")
            ui.select(
                label="Chart Type",
                value=self.widget_configuration.get("chart_type", "pie"),
                options=[
                    {"label": "Pie Chart", "value": "pie"},
                    {"label": "Donut Chart", "value": "donut"},
                    {"label": "Bar Chart", "value": "bar"},
                ],
                on_change=lambda e: self._update_configuration("chart_type", e.value),
            ).style("width:100%")

    def _update_configuration(self, key, value):
        self.widget_configuration[key] = value
        self.create_widget()

    def create_widget(self, widget_configuration=None):
        if widget_configuration:
            self.widget_configuration = widget_configuration
        elif not self.widget_configuration:
            self._set_default_configuration()

        if not self.widget_container:
            with ui.column().classes("w-full") as container:
                self.widget_container = container

        self.widget_container.clear()

        with self.widget_container:
            ui.label(self.widget_configuration["title"]).style(
                "font-size:1.5rem;font-weight:bold;"
            )

            chart_options = {
                "chart": {
                    "type": (
                        "pie"
                        if self.widget_configuration["chart_type"] in ["pie", "donut"]
                        else "bar"
                    ),
                },
                "title": {"text": ""},
                "tooltip": {
                    "pointFormat": "{series.name}: <b>{point.percentage:.1f}%</b>"
                },
                "accessibility": {"point": {"valueSuffix": "%"}},
                "plotOptions": {
                    "pie": {
                        "allowPointSelect": True,
                        "cursor": "pointer",
                        "dataLabels": {
                            "enabled": True,
                            "format": "<b>{point.name}</b>: {point.percentage:.1f} %",
                        },
                    }
                },
                "series": [
                    {
                        "name": "Balance Share",
                        "colorByPoint": True,
                        "data": self.chart_data,
                    }
                ],
            }

            if self.widget_configuration["chart_type"] == "donut":
                chart_options["plotOptions"]["pie"]["innerSize"] = "50%"

            ui.highchart(chart_options).classes("w-full h-96")

    def get_widget_details(self):
        return {
            "widget_id": self.widget_id,
            "widget_instance_id": self.widget_instance_id,
            "widget_name": self.widget_name,
            "widget_description": self.widget_description,
            "widget_configuration": self.widget_configuration,
        }
