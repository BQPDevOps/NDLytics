from datetime import datetime
import calendar
import pandas as pd
from nicegui import ui
from .BaseWGT import BaseWGT


class WGT_Prior_Month_Collections(BaseWGT):
    def __init__(
        self, dataframe_callback, widget_configuration=None, widget_instance_id=None
    ):
        self.get_dataframe = dataframe_callback
        super().__init__(widget_configuration, widget_instance_id)
        self.widget_id = "wgt_prior_month_collections"
        self.widget_name = "Prior Month Collections"
        self.widget_description = (
            "Displays previous month's collections with transaction details"
        )
        self.widget_icon = "history"

        self.transactions_df = None
        self.table_data = None
        self._onload()

    def _onload(self):
        self._set_default_configuration()
        self._process_data()

    def _set_default_configuration(self):
        if not self.widget_configuration:
            self.widget_configuration = {
                "title": "Prior Month Collections",
                "widget_width": 6,
                "max_rows": 10,
                "as_card": True,
            }

    def _process_data(self):
        # Load transactions data
        self.transactions_df = self.get_dataframe("datasets/primary/TR_Master.csv")

        # Convert dates
        self.transactions_df["posted_date"] = pd.to_datetime(
            self.transactions_df["posted_date"]
        )

        # Get previous month's date range
        today = datetime.now()
        if today.month == 1:
            prior_month = 12
            prior_year = today.year - 1
        else:
            prior_month = today.month - 1
            prior_year = today.year

        # Get first and last day of previous month
        first_day = datetime(prior_year, prior_month, 1)
        last_day = datetime(
            prior_year, prior_month, calendar.monthrange(prior_year, prior_month)[1]
        )

        # Filter for previous month's data
        prior_month_data = self.transactions_df[
            (self.transactions_df["posted_date"] >= first_day)
            & (self.transactions_df["posted_date"] <= last_day)
        ]

        # Sort by posted_date descending
        prior_month_data = prior_month_data.sort_values("posted_date", ascending=False)

        # Select required columns and prepare for display
        display_data = prior_month_data[
            [
                "file_number",
                "operator",
                "posted_date",
                "payment_amount",
                "contingency_amount",
            ]
        ]

        # Limit rows based on configuration - Convert max_rows to int
        max_rows = int(self.widget_configuration.get("max_rows", 10))
        display_data = display_data.iloc[:max_rows]

        # Convert to list of dictionaries for table display
        self.table_data = display_data.to_dict("records")

    def widget_configuration_form(self):
        with ui.column().classes("w-full gap-4"):
            ui.input(
                label="Widget Title",
                value=self.widget_configuration.get("title", "Prior Month Collections"),
                on_change=lambda e: self._update_configuration("title", e.value),
            ).classes("w-full")

            ui.slider(
                min=5,
                max=20,
                step=5,
                value=self.widget_configuration.get("max_rows", 10),
                on_change=lambda e: self._update_configuration("max_rows", e.value),
            ).classes("w-full").props("label label-always").bind_value_to(
                lambda: f"Show {self.widget_configuration.get('max_rows', 10)} Rows"
            )

            ui.switch(
                text="As Card",
                value=self.widget_configuration.get("as_card", True),
                on_change=lambda e: self._update_configuration("as_card", e.value),
            )

    def _update_configuration(self, key, value):
        self.widget_configuration[key] = value
        if key in ["max_rows"]:  # Refresh data when row limit changes
            self._process_data()
        self.create_widget()

    def _format_currency(self, value):
        """Format number as currency with padding"""
        basic_format = f"{value:,.2f}"
        return f"${basic_format:>15}"  # Right align with width of 15 (16 total with $)

    def widget_content(self):
        container_element = (
            ui.card().classes("w-full gap-4 rounded-lg")
            if self.widget_configuration.get("as_card", True)
            else ui.column().classes("w-full gap-4 p-[1rem]")
        )

        with container_element:
            ui.label(self.widget_configuration["title"]).classes("text-xl font-bold")

            # Calculate totals for the footer
            total_payments = sum(row["payment_amount"] for row in self.table_data)
            total_contingency = sum(
                row["contingency_amount"] for row in self.table_data
            )

            # Pre-format the data
            formatted_rows = []
            for row in self.table_data:
                formatted_rows.append(
                    {
                        "file_number": row["file_number"],
                        "operator": row["operator"],
                        "posted_date": row["posted_date"].strftime("%m/%d/%Y"),
                        "payment_amount": self._format_currency(row["payment_amount"]),
                        "contingency_amount": self._format_currency(
                            row["contingency_amount"]
                        ),
                    }
                )

            # Add totals row
            formatted_rows.append(
                {
                    "file_number": "",
                    "operator": "",
                    "posted_date": "TOTAL",
                    "payment_amount": self._format_currency(total_payments),
                    "contingency_amount": self._format_currency(total_contingency),
                }
            )

            # Create table headers
            columns = [
                {
                    "name": "file_number",
                    "label": "File Number",
                    "field": "file_number",
                    "align": "left",
                },
                {
                    "name": "operator",
                    "label": "Operator",
                    "field": "operator",
                    "align": "left",
                },
                {
                    "name": "posted_date",
                    "label": "Posted Date",
                    "field": "posted_date",
                    "align": "center",
                },
                {
                    "name": "payment_amount",
                    "label": "Payment Amount",
                    "field": "payment_amount",
                    "align": "right",
                },
                {
                    "name": "contingency_amount",
                    "label": "Contingency Amount",
                    "field": "contingency_amount",
                    "align": "right",
                },
            ]

            # Render table
            ui.table(
                columns=columns,
                rows=formatted_rows,
                row_key="file_number",
            ).classes("w-full").props("dense")

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
