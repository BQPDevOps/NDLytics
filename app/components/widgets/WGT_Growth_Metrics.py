from datetime import datetime, timedelta
import pandas as pd
from nicegui import ui
from .BaseWGT import BaseWGT


class WGT_Growth_Metrics(BaseWGT):
    def __init__(
        self, dataframe_callback, widget_configuration=None, widget_instance_id=None
    ):
        self.get_dataframe = dataframe_callback
        super().__init__(widget_configuration, widget_instance_id)
        self.widget_id = "wgt_growth_metrics"
        self.widget_name = "Growth Metrics"
        self.widget_description = (
            "Displays key collection metrics with month-over-month comparisons"
        )
        self.widget_icon = "trending_up"

        self.transactions_df = None
        self.metrics = {}
        self._onload()

    def _onload(self):
        self._set_default_configuration()
        self._process_data()

    def _set_default_configuration(self):
        if not self.widget_configuration:
            self.widget_configuration = {
                "title": "Collections Growth Metrics",
                "widget_width": 6,
                "show_percentage": True,
                "as_card": True,
            }

    def _process_data(self):
        # Load transactions data
        self.transactions_df = self.get_dataframe("datasets/primary/TR_Master.csv")

        # Convert dates
        self.transactions_df["posted_date"] = pd.to_datetime(
            self.transactions_df["posted_date"]
        )

        # Get current and previous month dates
        today = datetime.now()
        current_month_start = datetime(today.year, today.month, 1)
        prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

        # Filter for current and previous month
        current_month_data = self.transactions_df[
            self.transactions_df["posted_date"] >= current_month_start
        ]
        prev_month_data = self.transactions_df[
            (self.transactions_df["posted_date"] >= prev_month_start)
            & (self.transactions_df["posted_date"] < current_month_start)
        ]

        # Calculate metrics
        self.metrics = {
            "total_collections": {
                "current": current_month_data["payment_amount"].sum(),
                "previous": prev_month_data["payment_amount"].sum(),
                "label": "Total Collections",
                "format": "${:,.2f}",
            },
            "payment_count": {
                "current": len(current_month_data),
                "previous": len(prev_month_data),
                "label": "Payment Count",
                "format": "{:,}",
            },
            "average_payment": {
                "current": (
                    current_month_data["payment_amount"].mean()
                    if len(current_month_data) > 0
                    else 0
                ),
                "previous": (
                    prev_month_data["payment_amount"].mean()
                    if len(prev_month_data) > 0
                    else 0
                ),
                "label": "Average Payment",
                "format": "${:,.2f}",
            },
        }

    def _calculate_percentage_change(self, current, previous):
        if previous == 0:
            return float("inf") if current > 0 else 0
        return ((current - previous) / previous) * 100

    def widget_configuration_form(self):
        with ui.column().classes("w-full gap-4"):
            ui.input(
                label="Widget Title",
                value=self.widget_configuration.get(
                    "title", "Collections Growth Metrics"
                ),
                on_change=lambda e: self._update_configuration("title", e.value),
            )
            ui.switch(
                text="Show Percentage Changes",
                value=self.widget_configuration.get("show_percentage", True),
                on_change=lambda e: self._update_configuration(
                    "show_percentage", e.value
                ),
            )
            ui.switch(
                text="As Card",
                value=self.widget_configuration.get("as_card", True),
                on_change=lambda e: self._update_configuration("as_card", e.value),
            )

    def _update_configuration(self, key, value):
        self.widget_configuration[key] = value
        self.create_widget()

    def widget_content(self):
        container_element = (
            ui.card().classes("w-full gap-4 rounded-lg")
            if self.widget_configuration.get("as_card", True)
            else ui.column().classes("w-full gap-4 p-[1rem]")
        )
        with container_element:
            ui.label(self.widget_configuration["title"]).classes("text-xl font-bold")

            with ui.grid(columns=3).classes("w-full gap-4"):
                for metric_key, metric_data in self.metrics.items():
                    with ui.card().classes("w-full pl-4 pt-2 pb-4 pr-4 gap-1"):
                        with ui.row().classes(
                            "flex w-full items-center justify-center mb-2"
                        ):
                            ui.label(metric_data["label"]).classes("text-lg font-bold")

                        # Current month value
                        current_formatted = metric_data["format"].format(
                            metric_data["current"]
                        )
                        ui.label(f"Current: {current_formatted}").classes("text-lg")

                        # Previous month value
                        prev_formatted = metric_data["format"].format(
                            metric_data["previous"]
                        )
                        ui.label(f"Previous: {prev_formatted}").classes(
                            "text-[0.8rem] text-gray-600"
                        )

                        # Percentage change
                        if self.widget_configuration.get("show_percentage", True):
                            pct_change = self._calculate_percentage_change(
                                metric_data["current"], metric_data["previous"]
                            )

                            color = (
                                "text-green-600" if pct_change >= 0 else "text-red-600"
                            )
                            text_size = (
                                "text-sm" if abs(pct_change) < 100 else "text-[0.6rem]"
                            )
                            arrow = (
                                "o_arrow_drop_up"
                                if pct_change >= 0
                                else "o_arrow_drop_down"
                            )
                            with ui.row().classes("flex w-full items-end justify-end"):
                                with ui.card().tight().style(
                                    "gap:0;padding:0.5rem;border-radius:50%;height:3.2rem;width:3.2rem;display:flex;align-items:center;justify-content:center;flex-direction:column"
                                ):
                                    ui.label(f"{abs(pct_change):.1f}%").classes(
                                        f"{text_size} {color}"
                                    )
                                    ui.icon(arrow).classes(f"text-4xl h-[1rem] {color}")

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
