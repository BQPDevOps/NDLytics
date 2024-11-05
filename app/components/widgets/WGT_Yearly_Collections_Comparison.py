from datetime import datetime
import pandas as pd
from nicegui import ui
from .BaseWGT import BaseWGT


class WGT_Yearly_Collections_Comparison(BaseWGT):
    def __init__(
        self, dataframe_callback, widget_configuration=None, widget_instance_id=None
    ):
        self.get_dataframe = dataframe_callback
        super().__init__(widget_configuration, widget_instance_id)
        self.widget_id = "wgt_yearly_collections_comparison"
        self.widget_name = "Yearly Collections Comparison"
        self.widget_description = "Monthly collections with month-over-month comparison"
        self.widget_icon = "table_chart"

        self.transactions_df = None
        self.table_data = None
        self._onload()

    def _onload(self):
        self._set_default_configuration()
        self._process_data()

    def _set_default_configuration(self):
        if not self.widget_configuration:
            self.widget_configuration = {
                "title": "Yearly Collections Comparison",
                "widget_width": 6,
                "year": datetime.now().year,
                "as_card": True,
            }

    def _process_data(self):
        # Load transactions data
        self.transactions_df = self.get_dataframe("datasets/primary/TR_Master.csv")

        # Convert dates
        self.transactions_df["posted_date"] = pd.to_datetime(
            self.transactions_df["posted_date"]
        )

        # Filter for selected year
        year = self.widget_configuration.get("year", datetime.now().year)
        yearly_data = self.transactions_df[
            self.transactions_df["posted_date"].dt.year == year
        ]

        # Group by month and calculate total collections
        monthly_collections = (
            yearly_data.groupby(yearly_data["posted_date"].dt.month)["payment_amount"]
            .sum()
            .reindex(range(1, 13))
            .fillna(0)
        )

        # Calculate month-over-month changes
        mom_changes = monthly_collections.diff().fillna(0)

        # Create table data
        self.table_data = []
        running_total = 0

        for month in range(1, 13):
            month_total = monthly_collections.get(month, 0)
            running_total += month_total

            self.table_data.append(
                {
                    "month": datetime(2000, month, 1).strftime("%B"),
                    "total": month_total,
                    "mom_change": mom_changes.get(month, 0),
                    "ytd_total": running_total,
                }
            )

    def widget_configuration_form(self):
        with ui.column().classes("w-full gap-4"):
            ui.input(
                label="Widget Title",
                value=self.widget_configuration.get(
                    "title", "Yearly Collections Comparison"
                ),
                on_change=lambda e: self._update_configuration("title", e.value),
            ).classes("w-full")

            current_year = datetime.now().year
            ui.select(
                label="Year",
                options={
                    str(year): str(year)
                    for year in range(current_year - 2, current_year + 1)
                },
                value=str(self.widget_configuration.get("year", current_year)),
                on_change=lambda e: self._update_configuration("year", int(e.value)),
            ).classes("w-full")

            ui.switch(
                text="As Card",
                value=self.widget_configuration.get("as_card", True),
                on_change=lambda e: self._update_configuration("as_card", e.value),
            )

    def _update_configuration(self, key, value):
        self.widget_configuration[key] = value
        if key in ["year"]:  # Refresh data when year changes
            self._process_data()
        self.create_widget()

    def _format_currency(self, value):
        """Format number as currency with padding"""
        basic_format = f"{value:,.2f}"
        return f"${basic_format:>15}"  # Right align with width of 15 (16 total with $)

    def _format_change(self, value):
        """Format change value with sign"""
        sign = "+" if value > 0 else ""
        basic_format = f"{value:,.2f}"
        # Include sign in the padding calculation
        return f"${sign}{basic_format:>14}"  # Right align with width of 14 (16 total with $ and sign)

    def widget_content(self):
        container_element = (
            ui.card().classes("w-full gap-4 rounded-lg")
            if self.widget_configuration.get("as_card", True)
            else ui.column().classes("w-full gap-4 p-[1rem]")
        )

        with container_element:
            ui.label(self.widget_configuration["title"]).classes("text-xl font-bold")

            # Pre-format the data with simplified formatting
            formatted_rows = []
            for row in self.table_data:
                formatted_rows.append(
                    {
                        "month": row["month"],
                        "total": self._format_currency(row["total"]),
                        "mom_change": self._format_change(row["mom_change"]),
                        "ytd_total": self._format_currency(row["ytd_total"]),
                    }
                )

            # Create table headers without format functions
            columns = [
                {"name": "month", "label": "Month", "field": "month", "align": "left"},
                {
                    "name": "total",
                    "label": "Monthly Total",
                    "field": "total",
                    "align": "right",
                },
                {
                    "name": "mom_change",
                    "label": "Month over Month",
                    "field": "mom_change",
                    "align": "right",
                },
                {
                    "name": "ytd_total",
                    "label": "Running Total",
                    "field": "ytd_total",
                    "align": "right",
                },
            ]

            # Render table without HTML columns prop
            ui.table(
                columns=columns,
                rows=formatted_rows,
                row_key="month",
            ).classes(
                "w-full"
            ).props("dense")

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
